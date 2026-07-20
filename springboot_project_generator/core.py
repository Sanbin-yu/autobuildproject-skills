import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path


RESERVED_ENTITY_WORDS = {
    "backend",
    "management",
    "project",
    "system",
    "service",
    "application",
    "platform",
    "api",
    "with",
    "and",
}


@dataclass(frozen=True)
class ProjectNames:
    project_name: str
    project_class_name: str
    base_package: str
    common_module: str
    pojo_module: str
    server_module: str
    package_path: Path


@dataclass(frozen=True)
class FeatureOptions:
    security: bool = True
    jwt: bool = True
    redis: bool = True
    rabbitmq: bool = True
    mysql: bool = True
    mybatis_plus: bool = True


@dataclass(frozen=True)
class FieldSpec:
    name: str
    java_type: str = "String"
    required: bool = False
    unique: bool = False


@dataclass(frozen=True, eq=False)
class EntitySpec:
    name: str
    fields: list = field(default_factory=list)

    def __eq__(self, other):
        if isinstance(other, str):
            return self.name == other
        if isinstance(other, EntitySpec):
            return self.name == other.name and self.fields == other.fields
        return False


@dataclass(frozen=True)
class ProjectOptions:
    project_name: str
    description: str
    output_dir: Path
    base_package: str = None
    entities: list = field(default_factory=list)
    roles: list = field(default_factory=list)
    features: FeatureOptions = field(default_factory=FeatureOptions)
    java_version: str = "21"
    maven_version: str = "3.9"
    spring_boot_version: str = "3.3.5"
    mybatis_plus_version: str = "3.5.7"
    jwt_version: str = "0.12.6"


def slugify(value):
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    if not value:
        raise ValueError("Project name must contain at least one letter or digit")
    return value


def to_pascal_case(value):
    words = re.findall(r"[A-Z]+(?=[A-Z][a-z0-9]|$)|[A-Z]?[a-z0-9]+|[0-9]+", value)
    if not words:
        raise ValueError("Value must contain at least one letter or digit")
    return "".join(word[:1].upper() + word[1:].lower() for word in words)


def to_camel_case(value):
    pascal = to_pascal_case(value)
    return pascal[:1].lower() + pascal[1:]


def pluralize(value):
    lower = value.lower()
    if lower.endswith("y") and len(value) > 1 and lower[-2] not in "aeiou":
        return value[:-1] + "ies"
    if lower.endswith(("s", "x", "z", "ch", "sh")):
        return value + "es"
    return value + "s"


def table_name(entity_name):
    words = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z]|$)", entity_name)
    base = "_".join(word.lower() for word in words if word)
    return pluralize(base)


def derive_names(project_name, base_package):
    normalized = slugify(project_name)
    package = base_package or "com.example.%s" % normalized.replace("-", "")
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)+$", package):
        raise ValueError("Base package must be a valid Java package, for example com.example.demo")
    return ProjectNames(
        project_name=normalized,
        project_class_name=to_pascal_case(normalized),
        base_package=package,
        common_module="%s-common" % normalized,
        pojo_module="%s-pojo" % normalized,
        server_module="%s-server" % normalized,
        package_path=Path(*package.split(".")),
    )


def infer_entities(description):
    words = re.findall(r"[A-Za-z][A-Za-z0-9]*", description)
    candidates = []
    for word in words:
        lower = word.lower()
        if lower in RESERVED_ENTITY_WORDS:
            continue
        if lower.endswith("ing") or lower.endswith("ed"):
            continue
        entity = to_pascal_case(word)
        if entity not in candidates:
            candidates.append(entity)
        if len(candidates) == 3:
            break
    return candidates or ["Item"]


def detect_java_version():
    try:
        result = subprocess.run(
            ["java", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
    except OSError:
        return None
    text = result.stderr or result.stdout
    match = re.search(r'version "([0-9]+)', text)
    return match.group(1) if match else None


def detect_maven_version():
    try:
        result = subprocess.run(
            ["mvn", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            check=False,
        )
    except OSError:
        return None
    match = re.search(r"Apache Maven ([0-9]+(?:\.[0-9]+)+)", result.stdout)
    return match.group(1) if match else None


def load_project_config(config_path):
    config_path = Path(config_path)
    data = parse_simple_yaml(config_path.read_text(encoding="utf-8"))
    base_dir = config_path.parent
    output_dir = Path(data.get("outputDir", data.get("output_dir", ".")))
    if not output_dir.is_absolute():
        output_dir = base_dir / output_dir
    return ProjectOptions(
        project_name=require_config(data, "projectName"),
        base_package=data.get("basePackage"),
        description=data.get("description", ""),
        output_dir=output_dir,
        entities=parse_entity_specs(data.get("entities", [])),
        roles=[str(role) for role in data.get("roles", [])],
        features=parse_feature_options(data.get("features", {})),
        java_version=str(data.get("javaVersion", "21")),
        maven_version=str(data.get("mavenVersion", "3.9")),
        spring_boot_version=str(data.get("springBootVersion", "3.3.5")),
        mybatis_plus_version=str(data.get("mybatisPlusVersion", "3.5.7")),
        jwt_version=str(data.get("jwtVersion", "0.12.6")),
    )


def require_config(data, key):
    if key not in data or data[key] in ("", None):
        raise ValueError("Missing required config key: %s" % key)
    return data[key]


def parse_simple_yaml(text):
    lines = []
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        lines.append((indent, raw_line.strip()))
    if not lines:
        return {}
    value, index = parse_yaml_block(lines, 0, lines[0][0])
    if index != len(lines):
        raise ValueError("Unable to parse config near: %s" % lines[index][1])
    return value


def parse_yaml_block(lines, index, indent):
    if lines[index][1].startswith("- "):
        return parse_yaml_list(lines, index, indent)
    return parse_yaml_map(lines, index, indent)


def parse_yaml_map(lines, index, indent):
    data = {}
    while index < len(lines):
        line_indent, stripped = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ValueError("Unexpected indentation near: %s" % stripped)
        if stripped.startswith("- "):
            break
        if ":" not in stripped:
            raise ValueError("Invalid config line: %s" % stripped)
        key, value = stripped.split(":", 1)
        key = key.strip()
        value = value.strip()
        index += 1
        if value:
            data[key] = parse_scalar(value)
            continue
        if index < len(lines) and lines[index][0] > line_indent:
            child_indent = lines[index][0]
            data[key], index = parse_yaml_block(lines, index, child_indent)
        else:
            data[key] = []
    return data, index


def parse_yaml_list(lines, index, indent):
    values = []
    while index < len(lines):
        line_indent, stripped = lines[index]
        if line_indent < indent:
            break
        if line_indent > indent:
            raise ValueError("Unexpected indentation near: %s" % stripped)
        if not stripped.startswith("- "):
            break
        item_text = stripped[2:].strip()
        index += 1
        if not item_text:
            if index < len(lines) and lines[index][0] > line_indent:
                item, index = parse_yaml_block(lines, index, lines[index][0])
                values.append(item)
            else:
                values.append(None)
            continue
        if ":" in item_text:
            key, value = item_text.split(":", 1)
            item = {key.strip(): parse_scalar(value.strip()) if value.strip() else []}
            if not value.strip() and index < len(lines) and lines[index][0] > line_indent:
                item[key.strip()], index = parse_yaml_block(lines, index, lines[index][0])
            if index < len(lines) and lines[index][0] > line_indent:
                extra, index = parse_yaml_map(lines, index, lines[index][0])
                item.update(extra)
            values.append(item)
        else:
            values.append(parse_scalar(item_text))
    return values, index


def parse_scalar(value):
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
        return value[1:-1]
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    return value


def parse_feature_options(data):
    data = data or {}
    return FeatureOptions(
        security=bool_config(data.get("security", True)),
        jwt=bool_config(data.get("jwt", True)),
        redis=bool_config(data.get("redis", True)),
        rabbitmq=bool_config(data.get("rabbitmq", True)),
        mysql=bool_config(data.get("mysql", True)),
        mybatis_plus=bool_config(data.get("mybatisPlus", data.get("mybatis_plus", True))),
    )


def bool_config(value):
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in ("true", "1", "yes", "on")


def parse_entity_specs(values):
    specs = []
    for value in values:
        if isinstance(value, EntitySpec):
            specs.append(value)
        elif isinstance(value, str):
            specs.append(EntitySpec(to_pascal_case(value), default_entity_fields()))
        elif isinstance(value, dict):
            entity_name = value.get("name")
            if not entity_name:
                raise ValueError("Entity config must include name")
            fields = [parse_field_spec(field) for field in value.get("fields", [])]
            specs.append(EntitySpec(to_pascal_case(str(entity_name)), fields or default_entity_fields()))
        else:
            raise ValueError("Unsupported entity config: %s" % value)
    return specs


def parse_field_spec(value):
    if isinstance(value, str):
        if ":" in value:
            name, java_type = value.split(":", 1)
            return FieldSpec(normalize_field_name(name), java_type.strip() or "String")
        return FieldSpec(normalize_field_name(value))
    if isinstance(value, dict):
        return FieldSpec(
            name=normalize_field_name(require_config(value, "name")),
            java_type=str(value.get("type", value.get("javaType", "String"))),
            required=bool_config(value.get("required", False)),
            unique=bool_config(value.get("unique", False)),
        )
    raise ValueError("Unsupported field config: %s" % value)


def default_entity_fields():
    return [
        FieldSpec("name", "String", required=True),
        FieldSpec("description", "String"),
        FieldSpec("status", "Integer"),
    ]


def normalize_field_name(value):
    parts = re.findall(r"[A-Za-z0-9]+", str(value))
    if not parts:
        raise ValueError("Field name must contain at least one letter or digit")
    first = parts[0][:1].lower() + parts[0][1:]
    return first + "".join(part[:1].upper() + part[1:] for part in parts[1:])


def describe_plan(options):
    names = derive_names(options.project_name, options.base_package)
    entities = resolve_entity_specs(options)
    lines = [
        "Name: %s" % names.project_name,
        "Base package: %s" % names.base_package,
        "Modules: %s, %s, %s" % (names.common_module, names.pojo_module, names.server_module),
        "Java: %s" % options.java_version,
        "Maven: %s" % options.maven_version,
        "Spring Boot: %s" % options.spring_boot_version,
        "Entities: %s" % ", ".join(entity.name for entity in entities),
        "Output: %s" % (Path(options.output_dir) / names.project_name),
    ]
    return "\n".join(lines)


def generate_project(options):
    names = derive_names(options.project_name, options.base_package)
    entities = resolve_entity_specs(options)[:3]
    project_dir = Path(options.output_dir) / names.project_name
    if project_dir.exists():
        raise FileExistsError("Target directory already exists: %s" % project_dir)

    files = build_files(options, names, entities)
    for relative_path, content in files.items():
        path = project_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content.rstrip() + "\n", encoding="utf-8")

    return project_dir


def resolve_entity_specs(options):
    raw_entities = options.entities or infer_entities(options.description)
    return parse_entity_specs(raw_entities)


def build_files(options, names, entities):
    files = {
        ".gitignore": render_gitignore(),
        "README.md": render_project_readme(options, names, entities),
        "pom.xml": render_parent_pom(options, names),
        "%s/pom.xml" % names.common_module: render_common_pom(names),
        "%s/pom.xml" % names.pojo_module: render_pojo_pom(names),
        "%s/pom.xml" % names.server_module: render_server_pom(names),
        "%s/src/main/resources/application.yml" % names.server_module: render_application_yml(options, names),
        "%s/src/main/resources/db/schema.sql" % names.server_module: render_schema(entities),
    }

    package_dir = names.package_path
    common_base = Path(names.common_module) / "src/main/java" / package_dir
    pojo_base = Path(names.pojo_module) / "src/main/java" / package_dir
    server_base = Path(names.server_module) / "src/main/java" / package_dir
    server_test_base = Path(names.server_module) / "src/test/java" / package_dir

    add_common_files(files, common_base, names, options.roles, entities)
    add_pojo_files(files, pojo_base, names, entities, options.features)
    add_server_files(files, server_base, server_test_base, names, entities, options.features)
    add_empty_resource_dirs(files, names)
    return files


def uses_database_crud(features):
    return features.mysql and features.mybatis_plus


def add_empty_resource_dirs(files, names):
    # Maven ignores empty directories, so keep lightweight placeholders where useful.
    for module in [names.common_module, names.pojo_module]:
        files["%s/src/main/resources/.gitkeep" % module] = ""
        files["%s/src/test/java/.gitkeep" % module] = ""
    files["%s/src/test/resources/.gitkeep" % names.server_module] = ""


def put(files, path, content):
    files[str(path)] = content


def add_common_files(files, base, names, roles=None, entities=None):
    roles = normalize_roles(roles or [])
    entities = entities or []
    package = names.base_package
    put(files, base / "constant/MessageConstant.java", java(package, "constant", """
public final class MessageConstant {
    public static final String SUCCESS = "success";
    public static final String ERROR = "error";
    public static final String NOT_FOUND = "resource not found";
    public static final String VALIDATION_FAILED = "validation failed";

    private MessageConstant() {
    }
}
"""))
    put(files, base / "constant/StatusConstant.java", java(package, "constant", """
public final class StatusConstant {
    public static final int ENABLED = 1;
    public static final int DISABLED = 0;

    private StatusConstant() {
    }
}
"""))
    put(files, base / "constant/JwtClaimsConstant.java", java(package, "constant", """
public final class JwtClaimsConstant {
    public static final String USER_ID = "userId";
    public static final String ROLE = "role";

    private JwtClaimsConstant() {
    }
}
"""))
    if roles:
        put(files, base / "constant/RoleConstant.java", render_role_constant(package, roles))
    put(files, base / "constant/PermissionConstant.java", render_permission_constant(package, entities))
    put(files, base / "context/BaseContext.java", java(package, "context", """
public final class BaseContext {
    private static final ThreadLocal<Long> CURRENT_ID = new ThreadLocal<>();

    private BaseContext() {
    }

    public static void setCurrentId(Long id) {
        CURRENT_ID.set(id);
    }

    public static Long getCurrentId() {
        return CURRENT_ID.get();
    }

    public static void removeCurrentId() {
        CURRENT_ID.remove();
    }
}
"""))
    if roles:
        put(files, base / "context/AuthContext.java", render_auth_context(package))
    put(files, base / "enumeration/OperationType.java", java(package, "enumeration", """
public enum OperationType {
    CREATE,
    UPDATE,
    DELETE,
    QUERY
}
"""))
    put(files, base / "exception/BaseException.java", java(package, "exception", """
public class BaseException extends RuntimeException {
    public BaseException(String message) {
        super(message);
    }

    public BaseException(String message, Throwable cause) {
        super(message, cause);
    }
}
"""))
    put(files, base / "exception/BusinessException.java", java(package, "exception", """
public class BusinessException extends BaseException {
    public BusinessException(String message) {
        super(message);
    }
}
"""))
    put(files, base / "exception/NotFoundException.java", java(package, "exception", """
public class NotFoundException extends BaseException {
    public NotFoundException(String message) {
        super(message);
    }
}
"""))
    put(files, base / "json/JacksonObjectMapper.java", java(package, "json", """
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.datatype.jsr310.JavaTimeModule;

public class JacksonObjectMapper extends ObjectMapper {
    public JacksonObjectMapper() {
        registerModule(new JavaTimeModule());
    }
}
"""))
    put(files, base / "properties/JwtProperties.java", java(package, "properties", """
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "app.jwt")
public class JwtProperties {
    private String secret = "replace-this-secret-with-at-least-32-characters";
    private long ttlMinutes = 120;
}
"""))
    put(files, base / "properties/RedisProperties.java", java(package, "properties", """
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "app.redis")
public class RedisProperties {
    private boolean enabled = false;
}
"""))
    put(files, base / "properties/RabbitMqProperties.java", java(package, "properties", """
import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;

@Data
@ConfigurationProperties(prefix = "app.rabbitmq")
public class RabbitMqProperties {
    private boolean enabled = false;
}
"""))
    put(files, base / "result/Result.java", java(package, "result", """
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class Result<T> {
    private int code;
    private String message;
    private T data;

    public static <T> Result<T> success(T data) {
        return new Result<>(200, "success", data);
    }

    public static <T> Result<T> success() {
        return success(null);
    }

    public static <T> Result<T> error(String message) {
        return new Result<>(500, message, null);
    }
}
"""))
    put(files, base / "result/PageResult.java", java(package, "result", """
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class PageResult<T> {
    private long total;
    private List<T> records;
}
"""))
    put(files, base / "utils/JwtUtil.java", java(package, "utils", """
import java.nio.charset.StandardCharsets;
import java.time.Duration;
import java.time.Instant;
import java.util.Base64;
import javax.crypto.Mac;
import javax.crypto.spec.SecretKeySpec;

public final class JwtUtil {
    private JwtUtil() {
    }

    public static String createToken(String subject, String secret, Duration ttl) {
        String header = encode("{\\"alg\\":\\"HS256\\",\\"typ\\":\\"JWT\\"}");
        long expiresAt = Instant.now().plus(ttl).getEpochSecond();
        String payload = encode("{\\"sub\\":\\"" + subject + "\\",\\"exp\\":" + expiresAt + "}");
        String signature = hmacSha256(header + "." + payload, secret);
        return header + "." + payload + "." + signature;
    }

    private static String encode(String value) {
        return Base64.getUrlEncoder().withoutPadding()
                .encodeToString(value.getBytes(StandardCharsets.UTF_8));
    }

    private static String hmacSha256(String value, String secret) {
        try {
            Mac mac = Mac.getInstance("HmacSHA256");
            mac.init(new SecretKeySpec(secret.getBytes(StandardCharsets.UTF_8), "HmacSHA256"));
            return Base64.getUrlEncoder().withoutPadding()
                    .encodeToString(mac.doFinal(value.getBytes(StandardCharsets.UTF_8)));
        } catch (Exception ex) {
            throw new IllegalStateException("Unable to sign JWT", ex);
        }
    }
}
"""))
    put(files, base / "utils/AliOssUtil.java", java(package, "utils", """
public final class AliOssUtil {
    private AliOssUtil() {
    }

    public static String buildObjectUrl(String endpoint, String bucket, String objectName) {
        return "https://" + bucket + "." + endpoint + "/" + objectName;
    }
}
"""))
    put(files, base / "utils/HttpClientUtil.java", java(package, "utils", """
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

public final class HttpClientUtil {
    private static final HttpClient CLIENT = HttpClient.newHttpClient();

    private HttpClientUtil() {
    }

    public static String get(String url) {
        try {
            HttpRequest request = HttpRequest.newBuilder(URI.create(url)).GET().build();
            return CLIENT.send(request, HttpResponse.BodyHandlers.ofString()).body();
        } catch (Exception ex) {
            throw new IllegalStateException("HTTP request failed", ex);
        }
    }
}
"""))


def add_pojo_files(files, base, names, entities, features):
    package = names.base_package
    for entity in entities:
        variable = to_camel_case(entity.name)
        put(files, base / ("entity/%s.java" % entity.name), render_entity(package, entity, features))
        put(files, base / ("dto/%sDTO.java" % entity.name), render_dto(package, entity))
        put(files, base / ("dto/%sCreateDTO.java" % entity.name), render_create_dto(package, entity))
        put(files, base / ("dto/%sUpdateDTO.java" % entity.name), render_update_dto(package, entity))
        put(files, base / ("dto/%sQueryDTO.java" % entity.name), render_query_dto(package, entity))
        put(files, base / ("vo/%sVO.java" % entity.name), render_vo(package, entity))
        put(files, base / ("vo/%sListVO.java" % entity.name), render_list_vo(package, entity))
        put(files, base / ("vo/%sDetailVO.java" % entity.name), render_detail_vo(package, entity))
        put(files, base / ("dto/%sLoginDTO.java" % entity.name), render_login_dto(package, entity.name, variable))


def add_server_files(files, base, test_base, names, entities, features):
    package = names.base_package
    put(files, base / ("%sApplication.java" % names.project_class_name), render_application_class(package, names, features))
    if features.security:
        put(files, base / "config/SecurityConfig.java", render_security_config(package))
    put(files, base / "config/WebMvcConfiguration.java", render_web_mvc_config(package))
    put(files, base / "controller/HealthController.java", render_health_controller(package))
    put(files, base / "handler/GlobalExceptionHandler.java", render_exception_handler(package))
    if features.jwt:
        put(files, base / "interceptor/JwtTokenAdminInterceptor.java", render_interceptor(package))
    for entity in entities:
        put(files, base / ("controller/%sController.java" % entity.name), render_controller(package, entity))
        put(files, base / ("mapper/%sMapper.java" % entity.name), render_mapper(package, entity, features))
        put(files, base / ("service/%sService.java" % entity.name), render_service(package, entity))
        put(files, base / ("service/impl/%sServiceImpl.java" % entity.name), render_service_impl(package, entity, features))
    put(files, test_base / ("%sContextTest.java" % names.project_class_name), java(package, None, """
import org.junit.jupiter.api.Test;
import org.springframework.boot.test.context.SpringBootTest;

@SpringBootTest
class %sContextTest {
    @Test
    void contextLoads() {
    }
}
""" % names.project_class_name))
    if uses_database_crud(features):
        put(files, Path(names.server_module) / "src/test/resources/application.yml", render_test_application_yml(names))


def render_application_class(package, names, features):
    app_class = "%sApplication" % names.project_class_name
    if uses_database_crud(features):
        return java(package, None, """
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
public class %s {
    public static void main(String[] args) {
        SpringApplication.run(%s.class, args);
    }
}
""" % (app_class, app_class))
    return java(package, None, """
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;

@SpringBootApplication(exclude = DataSourceAutoConfiguration.class)
public class %s {
    public static void main(String[] args) {
        SpringApplication.run(%s.class, args);
    }
}
""" % (app_class, app_class))


def java(base_package, subpackage, body):
    package = base_package if subpackage is None else "%s.%s" % (base_package, subpackage)
    return "package %s;\n\n%s" % (package, body.strip())


def render_parent_pom(options, names):
    pom = render_template_file("maven/root-pom.xml.tpl", {
        "SPRING_BOOT_VERSION": options.spring_boot_version,
        "BASE_PACKAGE": names.base_package,
        "PROJECT_NAME": names.project_name,
        "DESCRIPTION": escape_xml(options.description),
        "COMMON_MODULE": names.common_module,
        "POJO_MODULE": names.pojo_module,
        "SERVER_MODULE": names.server_module,
        "JAVA_VERSION": options.java_version,
        "MYBATIS_PLUS_VERSION": options.mybatis_plus_version,
        "JWT_VERSION": options.jwt_version,
    })
    return filter_parent_pom_dependencies(pom, options.features)


def filter_parent_pom_dependencies(pom, features):
    disabled_artifacts = []
    if not features.security:
        disabled_artifacts.append("spring-boot-starter-security")
    if not features.mybatis_plus:
        disabled_artifacts.append("mybatis-plus-spring-boot3-starter")
    if not features.mysql:
        disabled_artifacts.append("mysql-connector-j")
    if not uses_database_crud(features):
        disabled_artifacts.append("h2")
    if not features.redis:
        disabled_artifacts.append("spring-boot-starter-data-redis")
    if not features.rabbitmq:
        disabled_artifacts.append("spring-boot-starter-amqp")
    if not features.jwt:
        disabled_artifacts.extend(["jjwt-api", "jjwt-impl", "jjwt-jackson"])
    for artifact_id in disabled_artifacts:
        pom = remove_dependency_block(pom, artifact_id)
    return pom


def remove_dependency_block(pom, artifact_id):
    pattern = re.compile(
        r"\n        <dependency>\n(?:(?!        </dependency>).)*?<artifactId>%s</artifactId>.*?\n        </dependency>" % re.escape(artifact_id),
        re.DOTALL,
    )
    return pattern.sub("", pom)


def default_parent_pom_template():
    return """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-parent</artifactId>
        <version>__SPRING_BOOT_VERSION__</version>
        <relativePath/>
    </parent>

    <groupId>__BASE_PACKAGE__</groupId>
    <artifactId>__PROJECT_NAME__</artifactId>
    <version>0.0.1-SNAPSHOT</version>
    <packaging>pom</packaging>
    <name>__PROJECT_NAME__</name>
    <description>__DESCRIPTION__</description>

    <modules>
        <module>__COMMON_MODULE__</module>
        <module>__POJO_MODULE__</module>
        <module>__SERVER_MODULE__</module>
    </modules>

    <properties>
        <java.version>__JAVA_VERSION__</java.version>
        <mybatis-plus.version>__MYBATIS_PLUS_VERSION__</mybatis-plus.version>
        <jjwt.version>__JWT_VERSION__</jjwt.version>
    </properties>

    <dependencies>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-web</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-validation</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-security</artifactId>
        </dependency>
        <dependency>
            <groupId>com.baomidou</groupId>
            <artifactId>mybatis-plus-spring-boot3-starter</artifactId>
            <version>${{mybatis-plus.version}}</version>
        </dependency>
        <dependency>
            <groupId>com.mysql</groupId>
            <artifactId>mysql-connector-j</artifactId>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>com.h2database</groupId>
            <artifactId>h2</artifactId>
            <scope>test</scope>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-data-redis</artifactId>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-amqp</artifactId>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-api</artifactId>
            <version>${{jjwt.version}}</version>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-impl</artifactId>
            <version>${{jjwt.version}}</version>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>io.jsonwebtoken</groupId>
            <artifactId>jjwt-jackson</artifactId>
            <version>${{jjwt.version}}</version>
            <scope>runtime</scope>
        </dependency>
        <dependency>
            <groupId>org.projectlombok</groupId>
            <artifactId>lombok</artifactId>
            <optional>true</optional>
        </dependency>
        <dependency>
            <groupId>org.springframework.boot</groupId>
            <artifactId>spring-boot-starter-test</artifactId>
            <scope>test</scope>
            <exclusions>
                <exclusion>
                    <groupId>org.mockito</groupId>
                    <artifactId>mockito-core</artifactId>
                </exclusion>
                <exclusion>
                    <groupId>org.mockito</groupId>
                    <artifactId>mockito-junit-jupiter</artifactId>
                </exclusion>
            </exclusions>
        </dependency>
    </dependencies>
</project>
"""


def render_common_pom(names):
    return child_pom(names, names.common_module)


def render_pojo_pom(names):
    return child_pom(names, names.pojo_module, dependencies=[
        (names.base_package, names.common_module, "${project.version}")
    ])


def render_server_pom(names):
    return child_pom(names, names.server_module, dependencies=[
        (names.base_package, names.common_module, "${project.version}"),
        (names.base_package, names.pojo_module, "${project.version}"),
    ], spring_boot_plugin=True)


def child_pom(names, artifact_id, dependencies=None, spring_boot_plugin=False):
    dependencies = dependencies or []
    dependency_text = "\n".join(
        """        <dependency>
            <groupId>%s</groupId>
            <artifactId>%s</artifactId>
            <version>%s</version>
        </dependency>""" % dependency
        for dependency in dependencies
    )
    build = ""
    if spring_boot_plugin:
        build = """
    <build>
        <plugins>
            <plugin>
                <groupId>org.springframework.boot</groupId>
                <artifactId>spring-boot-maven-plugin</artifactId>
            </plugin>
        </plugins>
    </build>
"""
    return """<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0"
         xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
         xsi:schemaLocation="http://maven.apache.org/POM/4.0.0 https://maven.apache.org/xsd/maven-4.0.0.xsd">
    <modelVersion>4.0.0</modelVersion>

    <parent>
        <groupId>{base_package}</groupId>
        <artifactId>{project_name}</artifactId>
        <version>0.0.1-SNAPSHOT</version>
    </parent>

    <artifactId>{artifact_id}</artifactId>
{dependencies_block}{build}</project>
""".format(
        base_package=names.base_package,
        project_name=names.project_name,
        artifact_id=artifact_id,
        dependencies_block=("\n    <dependencies>\n%s\n    </dependencies>\n" % dependency_text) if dependency_text else "",
        build=build,
    )


def render_gitignore():
    return """
target/
.idea/
*.iml
.DS_Store
logs/
*.log
"""


def normalize_roles(roles):
    normalized = []
    for role in roles:
        value = slugify(str(role)).replace("-", "_")
        if value not in normalized:
            normalized.append(value)
    return normalized


def constant_name(value):
    words = re.findall(r"[A-Za-z0-9]+", value)
    return "_".join(word.upper() for word in words)


def render_role_constant(package, roles):
    lines = [
        '    public static final String %s = "%s";' % (constant_name(role), role)
        for role in roles
    ]
    return java(package, "constant", """
public final class RoleConstant {
__ROLE_LINES__

    private RoleConstant() {
    }
}
""".replace("__ROLE_LINES__", "\n".join(lines)))


def render_permission_constant(package, entities):
    lines = []
    actions = ["CREATE", "UPDATE", "DELETE", "DETAIL", "PAGE"]
    for entity in entities:
        resource = to_camel_case(entity.name)
        for action in actions:
            lines.append('    public static final String %s_%s = "%s:%s";' % (
                constant_name(resource),
                action,
                resource,
                action.lower(),
            ))
    return java(package, "constant", """
public final class PermissionConstant {
__PERMISSION_LINES__

    private PermissionConstant() {
    }
}
""".replace("__PERMISSION_LINES__", "\n".join(lines)))


def render_auth_context(package):
    return java(package, "context", """
public final class AuthContext {
    private static final ThreadLocal<Long> CURRENT_USER_ID = new ThreadLocal<>();
    private static final ThreadLocal<String> CURRENT_ROLE = new ThreadLocal<>();

    private AuthContext() {
    }

    public static void setCurrentUserId(Long userId) {
        CURRENT_USER_ID.set(userId);
    }

    public static Long getCurrentUserId() {
        return CURRENT_USER_ID.get();
    }

    public static void setCurrentRole(String role) {
        CURRENT_ROLE.set(role);
    }

    public static String getCurrentRole() {
        return CURRENT_ROLE.get();
    }

    public static void clear() {
        CURRENT_USER_ID.remove();
        CURRENT_ROLE.remove();
    }
}
""")


def render_role_list(roles):
    normalized = normalize_roles(roles or [])
    if not normalized:
        return "- No roles configured yet; add `roles` in `project.yaml` when needed."
    return "\n".join("- `%s`" % role for role in normalized)


def render_project_readme(options, names, entities):
    return render_template_file("project/README.md.tpl", {
        "PROJECT_NAME": names.project_name,
        "DESCRIPTION": options.description,
        "COMMON_MODULE": names.common_module,
        "POJO_MODULE": names.pojo_module,
        "SERVER_MODULE": names.server_module,
        "ENTITY_LIST": "\n".join("- `%s`" % entity.name for entity in entities),
        "ROLE_LIST": render_role_list(options.roles),
        "JAVA_VERSION": options.java_version,
        "MAVEN_VERSION": options.maven_version,
        "SPRING_BOOT_VERSION": options.spring_boot_version,
    })


def default_project_readme_template():
    return """# __PROJECT_NAME__

__DESCRIPTION__

## Modules

- `__COMMON_MODULE__`: constants, context, enums, exceptions, JSON helpers, properties, result wrappers, utilities.
- `__POJO_MODULE__`: entity, DTO, and VO classes.
- `__SERVER_MODULE__`: Spring Boot application, controllers, services, mappers, handlers, interceptors, and configuration.

## Generated Business Objects

__ENTITY_LIST__

## Generated Roles

__ROLE_LIST__

## Environment

- Java: __JAVA_VERSION__
- Maven: __MAVEN_VERSION__
- Spring Boot: __SPRING_BOOT_VERSION__

## Run

```bash
mvn test
mvn package
mvn -pl __SERVER_MODULE__ spring-boot:run
```

Database persistence is generated with MyBatis-Plus mapper calls and `src/main/resources/db/schema.sql`. `mvn test` uses the generated H2 test datasource; configure a live MySQL datasource before running the server in database mode.

## Configuration

- `app.security.enabled`: default `false`; set to `true` to require authentication for non-health routes.
- `app.jwt.secret`: replace before production use.
- `app.redis.enabled`: default `false`.
- `app.rabbitmq.enabled`: default `false`.
"""


def render_application_yml(options, names):
    return render_template_file("resources/application.yml.tpl", {
        "PROJECT_NAME": names.project_name,
    })


def render_test_application_yml(names):
    database_name = re.sub(r"[^A-Za-z0-9_]", "_", names.project_name)
    return """spring:
  datasource:
    url: jdbc:h2:mem:%s;MODE=MySQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1
    driver-class-name: org.h2.Driver
    username: sa
    password:
  sql:
    init:
      mode: always
      schema-locations: classpath:db/schema.sql
""" % database_name


def default_application_yml_template():
    return """server:
  port: 8080

spring:
  application:
    name: __PROJECT_NAME__

app:
  security:
    enabled: false
  jwt:
    secret: replace-this-secret-with-at-least-32-characters
    ttl-minutes: 120
  redis:
    enabled: false
  rabbitmq:
    enabled: false
"""


def render_template_file(relative_path, values):
    template = read_template(relative_path)
    return replace_tokens(template, **values)


def read_template(relative_path):
    template_path = Path(__file__).resolve().parents[1] / "templates" / relative_path
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    defaults = {
        "maven/root-pom.xml.tpl": default_parent_pom_template,
        "project/README.md.tpl": default_project_readme_template,
        "resources/application.yml.tpl": default_application_yml_template,
    }
    if relative_path not in defaults:
        raise FileNotFoundError("Template not found: %s" % relative_path)
    return defaults[relative_path]()


def render_schema(entities):
    chunks = []
    for entity in entities:
        field_lines = []
        unique_lines = []
        table = table_name(entity.name)
        for field_spec in entity.fields:
            column = column_name(field_spec.name)
            field_lines.append("    %s %s%s," % (
                column,
                sql_type(field_spec.java_type),
                " NOT NULL" if field_spec.required else "",
            ))
            if field_spec.unique:
                unique_lines.append("    UNIQUE KEY uk_%s_%s (%s)" % (table, column, column))
        lines = [
            "CREATE TABLE IF NOT EXISTS %s (" % table,
            "    id BIGINT PRIMARY KEY AUTO_INCREMENT,",
        ]
        lines.extend(field_lines)
        lines.append("    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,")
        if unique_lines:
            lines.append("    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,")
            lines.extend("%s%s" % (line, "," if index < len(unique_lines) - 1 else "")
                         for index, line in enumerate(unique_lines))
        else:
            lines.append("    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")
        lines.append(");")
        chunks.append("\n".join(lines))
    return "\n\n".join(chunks)


def render_entity(package, entity, features):
    imports = [
        "import java.time.LocalDateTime;",
        "import lombok.AllArgsConstructor;",
        "import lombok.Builder;",
        "import lombok.Data;",
        "import lombok.NoArgsConstructor;",
    ]
    imports.extend(java_type_imports(entity.fields))
    if features.mybatis_plus:
        imports = [
            "import com.baomidou.mybatisplus.annotation.IdType;",
            "import com.baomidou.mybatisplus.annotation.TableId;",
            "import com.baomidou.mybatisplus.annotation.TableName;",
        ] + imports
    annotation = '@TableName("%s")\n' % table_name(entity.name) if features.mybatis_plus else ""
    id_annotation = "    @TableId(type = IdType.AUTO)\n" if features.mybatis_plus else ""
    return java(package, "entity", """
__IMPORTS__

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
__ANNOTATION__public class __ENTITY__ {
__ID_ANNOTATION__    private Long id;
__FIELDS__
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
""".replace("__IMPORTS__", join_imports(imports))
        .replace("__ANNOTATION__", annotation)
        .replace("__ENTITY__", entity.name)
        .replace("__ID_ANNOTATION__", id_annotation)
        .replace("__FIELDS__", render_field_declarations(entity.fields)))


def render_dto(package, entity):
    imports = ["import lombok.Data;"] + java_type_imports(entity.fields)
    return java(package, "dto", """
__IMPORTS__

@Data
public class __ENTITY__DTO {
__FIELDS__
}
""".replace("__IMPORTS__", join_imports(imports))
        .replace("__ENTITY__", entity.name)
        .replace("__FIELDS__", render_field_declarations(entity.fields)))


def render_create_dto(package, entity):
    imports = ["import lombok.Data;"] + validation_type_imports(entity.fields) + java_type_imports(entity.fields)
    return java(package, "dto", """
__IMPORTS__

@Data
public class __ENTITY__CreateDTO {
__FIELDS__
}
""".replace("__IMPORTS__", join_imports(imports))
        .replace("__ENTITY__", entity.name)
        .replace("__FIELDS__", render_field_declarations(entity.fields, include_validation=True)))


def render_update_dto(package, entity):
    imports = [
        "import jakarta.validation.constraints.NotNull;",
        "import lombok.Data;",
    ] + java_type_imports(entity.fields)
    return java(package, "dto", """
__IMPORTS__

@Data
public class __ENTITY__UpdateDTO {
    @NotNull
    private Long id;
__FIELDS__
}
""".replace("__IMPORTS__", join_imports(imports))
        .replace("__ENTITY__", entity.name)
        .replace("__FIELDS__", render_field_declarations(entity.fields)))


def render_query_dto(package, entity):
    return java(package, "dto", """
import lombok.Data;

@Data
public class %sQueryDTO {
    private String keyword;
    private Integer page = 1;
    private Integer pageSize = 10;
}
""" % entity.name)


def render_login_dto(package, entity, variable):
    return java(package, "dto", """
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

@Data
public class %sLoginDTO {
    @NotBlank
    private String username;
    @NotBlank
    private String password;
}
""" % entity)


def render_vo(package, entity):
    imports = [
        "import java.time.LocalDateTime;",
        "import lombok.Builder;",
        "import lombok.Data;",
    ] + java_type_imports(entity.fields, include_local_date_time=False)
    return java(package, "vo", """
__IMPORTS__

@Data
@Builder
public class __ENTITY__VO {
    private Long id;
__FIELDS__
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
""".replace("__IMPORTS__", join_imports(imports))
        .replace("__ENTITY__", entity.name)
        .replace("__FIELDS__", render_field_declarations(entity.fields)))


def render_list_vo(package, entity):
    imports = ["import lombok.Builder;", "import lombok.Data;"] + java_type_imports(list_fields(entity.fields))
    return java(package, "vo", """
__IMPORTS__

@Data
@Builder
public class __ENTITY__ListVO {
    private Long id;
__FIELDS__
}
""".replace("__IMPORTS__", join_imports(imports))
        .replace("__ENTITY__", entity.name)
        .replace("__FIELDS__", render_field_declarations(list_fields(entity.fields))))


def render_detail_vo(package, entity):
    imports = [
        "import java.time.LocalDateTime;",
        "import lombok.Builder;",
        "import lombok.Data;",
    ] + java_type_imports(entity.fields, include_local_date_time=False)
    return java(package, "vo", """
__IMPORTS__

@Data
@Builder
public class __ENTITY__DetailVO {
    private Long id;
__FIELDS__
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
""".replace("__IMPORTS__", join_imports(imports))
        .replace("__ENTITY__", entity.name)
        .replace("__FIELDS__", render_field_declarations(entity.fields)))


def render_controller(package, entity):
    variable = to_camel_case(entity.name)
    path = table_name(entity.name).replace("_", "-")
    body = """
import __PACKAGE__.dto.__ENTITY__CreateDTO;
import __PACKAGE__.dto.__ENTITY__QueryDTO;
import __PACKAGE__.dto.__ENTITY__UpdateDTO;
import __PACKAGE__.result.PageResult;
import __PACKAGE__.result.Result;
import __PACKAGE__.service.__ENTITY__Service;
import __PACKAGE__.vo.__ENTITY__DetailVO;
import __PACKAGE__.vo.__ENTITY__ListVO;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/__PATH__")
public class __ENTITY__Controller {
    private final __ENTITY__Service __VARIABLE__Service;

    @PostMapping
    public Result<__ENTITY__DetailVO> create(@Valid @RequestBody __ENTITY__CreateDTO dto) {
        return Result.success(__VARIABLE__Service.create(dto));
    }

    @GetMapping("/{id}")
    public Result<__ENTITY__DetailVO> getById(@PathVariable Long id) {
        return Result.success(__VARIABLE__Service.getById(id));
    }

    @GetMapping
    public Result<PageResult<__ENTITY__ListVO>> page(__ENTITY__QueryDTO query) {
        return Result.success(__VARIABLE__Service.page(query));
    }

    @PutMapping
    public Result<__ENTITY__DetailVO> update(@Valid @RequestBody __ENTITY__UpdateDTO dto) {
        return Result.success(__VARIABLE__Service.update(dto));
    }

    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        __VARIABLE__Service.delete(id);
        return Result.success();
    }
}
"""
    return java(package, "controller", replace_tokens(
        body,
        PACKAGE=package,
        ENTITY=entity.name,
        VARIABLE=variable,
        PATH=path,
    ))


def render_mapper(package, entity, features):
    if not features.mybatis_plus:
        return java(package, "mapper", """
import %s.entity.%s;

public interface %sMapper {
}
""" % (package, entity.name, entity.name))
    return java(package, "mapper", """
import %s.entity.%s;
import com.baomidou.mybatisplus.core.mapper.BaseMapper;
import org.apache.ibatis.annotations.Mapper;

@Mapper
public interface %sMapper extends BaseMapper<%s> {
}
""" % (package, entity.name, entity.name, entity.name))


def render_service(package, entity):
    return java(package, "service", """
import %s.dto.%sCreateDTO;
import %s.dto.%sQueryDTO;
import %s.dto.%sUpdateDTO;
import %s.result.PageResult;
import %s.vo.%sDetailVO;
import %s.vo.%sListVO;

public interface %sService {
    %sDetailVO create(%sCreateDTO dto);

    %sDetailVO getById(Long id);

    PageResult<%sListVO> page(%sQueryDTO query);

    %sDetailVO update(%sUpdateDTO dto);

    void delete(Long id);
}
""" % (
        package, entity.name,
        package, entity.name,
        package, entity.name,
        package,
        package, entity.name,
        package, entity.name,
        entity.name,
        entity.name, entity.name,
        entity.name,
        entity.name, entity.name,
        entity.name, entity.name,
    ))


def render_service_impl(package, entity, features):
    if uses_database_crud(features):
        return render_database_service_impl(package, entity)
    return render_in_memory_service_impl(package, entity)


def render_database_service_impl(package, entity):
    variable = to_camel_case(entity.name)
    body = """
import __PACKAGE__.dto.__ENTITY__CreateDTO;
import __PACKAGE__.dto.__ENTITY__QueryDTO;
import __PACKAGE__.dto.__ENTITY__UpdateDTO;
import __PACKAGE__.entity.__ENTITY__;
import __PACKAGE__.exception.NotFoundException;
import __PACKAGE__.mapper.__ENTITY__Mapper;
import __PACKAGE__.result.PageResult;
import __PACKAGE__.service.__ENTITY__Service;
import __PACKAGE__.vo.__ENTITY__DetailVO;
import __PACKAGE__.vo.__ENTITY__ListVO;
import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
@RequiredArgsConstructor
public class __ENTITY__ServiceImpl implements __ENTITY__Service {
    private final __ENTITY__Mapper __VARIABLE__Mapper;

    @Override
    public __ENTITY__DetailVO create(__ENTITY__CreateDTO dto) {
        LocalDateTime now = LocalDateTime.now();
        __ENTITY__ __VARIABLE__ = __ENTITY__.builder()
__CREATE_ASSIGNMENTS__
                .createdAt(now)
                .updatedAt(now)
                .build();
        __VARIABLE__Mapper.insert(__VARIABLE__);
        return toDetailVO(__VARIABLE__);
    }

    @Override
    public __ENTITY__DetailVO getById(Long id) {
        return toDetailVO(find(id));
    }

    @Override
    public PageResult<__ENTITY__ListVO> page(__ENTITY__QueryDTO query) {
        int page = query.getPage() == null || query.getPage() < 1 ? 1 : query.getPage();
        int pageSize = query.getPageSize() == null || query.getPageSize() < 1 ? 10 : query.getPageSize();
        Page<__ENTITY__> pageRequest = new Page<>(page, pageSize);
        QueryWrapper<__ENTITY__> queryWrapper = new QueryWrapper<>();
        String keyword = query.getKeyword();
__QUERY_WRAPPER_KEYWORD_BLOCK__
        queryWrapper.orderByAsc("id");
        Page<__ENTITY__> result = __VARIABLE__Mapper.selectPage(pageRequest, queryWrapper);
        List<__ENTITY__ListVO> records = result.getRecords().stream()
                .map(this::toListVO)
                .collect(Collectors.toList());
        return new PageResult<>(result.getTotal(), records);
    }

    @Override
    public __ENTITY__DetailVO update(__ENTITY__UpdateDTO dto) {
        __ENTITY__ existing = find(dto.getId());
__UPDATE_ASSIGNMENTS__
        existing.setUpdatedAt(LocalDateTime.now());
        __VARIABLE__Mapper.updateById(existing);
        return toDetailVO(existing);
    }

    @Override
    public void delete(Long id) {
        if (__VARIABLE__Mapper.deleteById(id) == 0) {
            throw new NotFoundException("__ENTITY__ not found: " + id);
        }
    }

    private __ENTITY__ find(Long id) {
        __ENTITY__ item = __VARIABLE__Mapper.selectById(id);
        if (item == null) {
            throw new NotFoundException("__ENTITY__ not found: " + id);
        }
        return item;
    }

    private __ENTITY__ListVO toListVO(__ENTITY__ item) {
        return __ENTITY__ListVO.builder()
                .id(item.getId())
__LIST_VO_ASSIGNMENTS__
                .build();
    }

    private __ENTITY__DetailVO toDetailVO(__ENTITY__ item) {
        return __ENTITY__DetailVO.builder()
                .id(item.getId())
__DETAIL_VO_ASSIGNMENTS__
                .createdAt(item.getCreatedAt())
                .updatedAt(item.getUpdatedAt())
                .build();
    }
}
"""
    return java(package, "service.impl", replace_tokens(
        body,
        PACKAGE=package,
        ENTITY=entity.name,
        VARIABLE=variable,
        CREATE_ASSIGNMENTS=builder_assignments_from_dto(entity.fields),
        UPDATE_ASSIGNMENTS=update_assignments_from_dto(entity.fields),
        QUERY_WRAPPER_KEYWORD_BLOCK=query_wrapper_keyword_block(entity.fields),
        LIST_VO_ASSIGNMENTS=builder_assignments_from_item(list_fields(entity.fields)),
        DETAIL_VO_ASSIGNMENTS=builder_assignments_from_item(entity.fields),
    ))


def render_in_memory_service_impl(package, entity):
    variable = to_camel_case(entity.name)
    body = """
import __PACKAGE__.dto.__ENTITY__CreateDTO;
import __PACKAGE__.dto.__ENTITY__QueryDTO;
import __PACKAGE__.dto.__ENTITY__UpdateDTO;
import __PACKAGE__.entity.__ENTITY__;
import __PACKAGE__.exception.NotFoundException;
import __PACKAGE__.result.PageResult;
import __PACKAGE__.service.__ENTITY__Service;
import __PACKAGE__.vo.__ENTITY__DetailVO;
import __PACKAGE__.vo.__ENTITY__ListVO;
import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.util.StringUtils;

@Service
public class __ENTITY__ServiceImpl implements __ENTITY__Service {
    private final AtomicLong ids = new AtomicLong(1);
    private final Map<Long, __ENTITY__> store = new ConcurrentHashMap<>();

    @Override
    public __ENTITY__DetailVO create(__ENTITY__CreateDTO dto) {
        LocalDateTime now = LocalDateTime.now();
        __ENTITY__ __VARIABLE__ = __ENTITY__.builder()
                .id(ids.getAndIncrement())
__CREATE_ASSIGNMENTS__
                .createdAt(now)
                .updatedAt(now)
                .build();
        store.put(__VARIABLE__.getId(), __VARIABLE__);
        return toDetailVO(__VARIABLE__);
    }

    @Override
    public __ENTITY__DetailVO getById(Long id) {
        return toDetailVO(find(id));
    }

    @Override
    public PageResult<__ENTITY__ListVO> page(__ENTITY__QueryDTO query) {
        int page = query.getPage() == null || query.getPage() < 1 ? 1 : query.getPage();
        int pageSize = query.getPageSize() == null || query.getPageSize() < 1 ? 10 : query.getPageSize();
        String keyword = query.getKeyword();
        List<__ENTITY__ListVO> records = store.values().stream()
                .filter(item -> matchesKeyword(item, keyword))
                .sorted(Comparator.comparing(__ENTITY__::getId))
                .map(this::toListVO)
                .collect(Collectors.toList());
        int fromIndex = Math.min((page - 1) * pageSize, records.size());
        int toIndex = Math.min(fromIndex + pageSize, records.size());
        return new PageResult<>(records.size(), new ArrayList<>(records.subList(fromIndex, toIndex)));
    }

    @Override
    public __ENTITY__DetailVO update(__ENTITY__UpdateDTO dto) {
        __ENTITY__ existing = find(dto.getId());
__UPDATE_ASSIGNMENTS__
        existing.setUpdatedAt(LocalDateTime.now());
        return toDetailVO(existing);
    }

    @Override
    public void delete(Long id) {
        if (store.remove(id) == null) {
            throw new NotFoundException("__ENTITY__ not found: " + id);
        }
    }

    private __ENTITY__ find(Long id) {
        __ENTITY__ item = store.get(id);
        if (item == null) {
            throw new NotFoundException("__ENTITY__ not found: " + id);
        }
        return item;
    }

    private boolean matchesKeyword(__ENTITY__ item, String keyword) {
        return !StringUtils.hasText(keyword)__KEYWORD_MATCH__;
    }

    private __ENTITY__ListVO toListVO(__ENTITY__ item) {
        return __ENTITY__ListVO.builder()
                .id(item.getId())
__LIST_VO_ASSIGNMENTS__
                .build();
    }

    private __ENTITY__DetailVO toDetailVO(__ENTITY__ item) {
        return __ENTITY__DetailVO.builder()
                .id(item.getId())
__DETAIL_VO_ASSIGNMENTS__
                .createdAt(item.getCreatedAt())
                .updatedAt(item.getUpdatedAt())
                .build();
    }
}
"""
    return java(package, "service.impl", replace_tokens(
        body,
        PACKAGE=package,
        ENTITY=entity.name,
        VARIABLE=variable,
        CREATE_ASSIGNMENTS=builder_assignments_from_dto(entity.fields),
        UPDATE_ASSIGNMENTS=update_assignments_from_dto(entity.fields),
        KEYWORD_MATCH=keyword_match_expression(entity.fields),
        LIST_VO_ASSIGNMENTS=builder_assignments_from_item(list_fields(entity.fields)),
        DETAIL_VO_ASSIGNMENTS=builder_assignments_from_item(entity.fields),
    ))


def render_field_declarations(fields, include_validation=False):
    lines = []
    for field_spec in fields:
        if include_validation and field_spec.required:
            annotation = validation_annotation(field_spec.java_type)
            if annotation:
                lines.append("    %s" % annotation)
        lines.append("    private %s %s;" % (field_spec.java_type, field_spec.name))
    return "\n".join(lines)


def java_type_imports(fields, include_local_date_time=True):
    imports = []
    type_imports = {
        "BigDecimal": "import java.math.BigDecimal;",
        "LocalDate": "import java.time.LocalDate;",
        "LocalDateTime": "import java.time.LocalDateTime;",
    }
    for field_spec in fields:
        if field_spec.java_type == "LocalDateTime" and not include_local_date_time:
            continue
        if field_spec.java_type in type_imports:
            imports.append(type_imports[field_spec.java_type])
    return imports


def validation_type_imports(fields):
    imports = []
    for field_spec in fields:
        if not field_spec.required:
            continue
        if field_spec.java_type == "String":
            imports.append("import jakarta.validation.constraints.NotBlank;")
        else:
            imports.append("import jakarta.validation.constraints.NotNull;")
    return imports


def validation_annotation(java_type):
    if java_type == "String":
        return "@NotBlank"
    return "@NotNull"


def join_imports(imports):
    seen = []
    for import_line in imports:
        if import_line and import_line not in seen:
            seen.append(import_line)
    return "\n".join(seen)


def list_fields(fields):
    return fields[:4]


def column_name(field_name):
    words = re.findall(r"[A-Z]?[a-z0-9]+|[A-Z]+(?=[A-Z]|$)", field_name)
    return "_".join(word.lower() for word in words if word)


def sql_type(java_type):
    mapping = {
        "String": "VARCHAR(255)",
        "Integer": "INT",
        "Long": "BIGINT",
        "BigDecimal": "DECIMAL(18, 2)",
        "LocalDateTime": "DATETIME",
        "LocalDate": "DATE",
        "Boolean": "TINYINT(1)",
        "Double": "DOUBLE",
    }
    return mapping.get(java_type, "VARCHAR(255)")


def getter_name(field_spec):
    prefix = "get"
    return "%s%s" % (prefix, field_spec.name[:1].upper() + field_spec.name[1:])


def setter_name(field_spec):
    return "set%s%s" % (field_spec.name[:1].upper(), field_spec.name[1:])


def builder_assignments_from_dto(fields):
    return "\n".join(
        "                .%s(dto.%s())" % (field_spec.name, getter_name(field_spec))
        for field_spec in fields
    )


def builder_assignments_from_item(fields):
    return "\n".join(
        "                .%s(item.%s())" % (field_spec.name, getter_name(field_spec))
        for field_spec in fields
    )


def update_assignments_from_dto(fields):
    blocks = []
    for field_spec in fields:
        getter = getter_name(field_spec)
        setter = setter_name(field_spec)
        if field_spec.java_type == "String":
            blocks.append("""        if (StringUtils.hasText(dto.%s())) {
            existing.%s(dto.%s());
        }""" % (getter, setter, getter))
        else:
            blocks.append("""        if (dto.%s() != null) {
            existing.%s(dto.%s());
        }""" % (getter, setter, getter))
    return "\n".join(blocks)


def query_wrapper_keyword_block(fields):
    string_fields = [field_spec for field_spec in fields if field_spec.java_type == "String"][:3]
    if not string_fields:
        return ""
    if len(string_fields) == 1:
        return """        if (StringUtils.hasText(keyword)) {
            queryWrapper.like("%s", keyword);
        }""" % column_name(string_fields[0].name)
    lines = [
        "        if (StringUtils.hasText(keyword)) {",
        "            queryWrapper.and(wrapper -> wrapper",
    ]
    for index, field_spec in enumerate(string_fields):
        if index:
            lines.append("                    .or()")
        suffix = ");" if index == len(string_fields) - 1 else ""
        lines.append('                    .like("%s", keyword)%s' % (column_name(field_spec.name), suffix))
    lines.append("        }")
    return "\n".join(lines)


def keyword_match_expression(fields):
    string_fields = [field_spec for field_spec in fields if field_spec.java_type == "String"]
    if not string_fields:
        return ""
    checks = [
        "\n                || (item.%s() != null && item.%s().toLowerCase().contains(keyword.toLowerCase()))" % (
            getter_name(field_spec),
            getter_name(field_spec),
        )
        for field_spec in string_fields[:3]
    ]
    return "".join(checks)


def replace_tokens(template, **values):
    for key, value in values.items():
        template = template.replace("__%s__" % key, value)
    return template


def render_security_config(package):
    return java(package, "config", """
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Value("${app.security.enabled:false}")
    private boolean securityEnabled;

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http.csrf(AbstractHttpConfigurer::disable);
        if (securityEnabled) {
            http.authorizeHttpRequests(auth -> auth
                    .requestMatchers("/api/health").permitAll()
                    .anyRequest().authenticated());
        } else {
            http.authorizeHttpRequests(auth -> auth.anyRequest().permitAll());
        }
        return http.build();
    }
}
""")


def render_web_mvc_config(package):
    return java(package, "config", """
import %s.json.JacksonObjectMapper;
import org.springframework.boot.autoconfigure.jackson.Jackson2ObjectMapperBuilderCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class WebMvcConfiguration {
    @Bean
    public Jackson2ObjectMapperBuilderCustomizer jacksonCustomizer() {
        return builder -> builder.configure(new JacksonObjectMapper());
    }
}
""" % package)


def render_health_controller(package):
    return java(package, "controller", """
import %s.result.Result;
import java.util.Map;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/health")
public class HealthController {
    @GetMapping
    public Result<Map<String, String>> health() {
        return Result.success(Map.of("status", "UP"));
    }
}
""" % package)


def render_exception_handler(package):
    return java(package, "handler", """
import %s.exception.BaseException;
import %s.result.Result;
import org.springframework.validation.BindException;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

@RestControllerAdvice
public class GlobalExceptionHandler {
    @ExceptionHandler(BaseException.class)
    public Result<Void> handleBaseException(BaseException ex) {
        return Result.error(ex.getMessage());
    }

    @ExceptionHandler({MethodArgumentNotValidException.class, BindException.class})
    public Result<Void> handleValidationException(Exception ex) {
        return Result.error("validation failed");
    }
}
""" % (package, package))


def render_interceptor(package):
    return java(package, "interceptor", """
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class JwtTokenAdminInterceptor implements HandlerInterceptor {
    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        return true;
    }
}
""")


def escape_xml(value):
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )
