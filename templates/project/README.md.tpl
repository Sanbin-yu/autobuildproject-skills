# __PROJECT_NAME__

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
