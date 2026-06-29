server:
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

