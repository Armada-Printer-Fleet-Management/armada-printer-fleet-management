window.OPENAPI_SPEC = {
  "components": {
    "schemas": {
      "HTTPValidationError": {
        "properties": {
          "detail": {
            "items": {
              "$ref": "#/components/schemas/ValidationError"
            },
            "title": "Detail",
            "type": "array"
          }
        },
        "title": "HTTPValidationError",
        "type": "object"
      },
      "HealthResponse": {
        "properties": {
          "dependencies": {
            "anyOf": [
              {
                "additionalProperties": {
                  "type": "string"
                },
                "type": "object"
              },
              {
                "type": "null"
              }
            ],
            "title": "Dependencies"
          },
          "status": {
            "$ref": "#/components/schemas/HealthStatus"
          },
          "version": {
            "anyOf": [
              {
                "type": "string"
              },
              {
                "type": "null"
              }
            ],
            "title": "Version"
          }
        },
        "required": [
          "status"
        ],
        "title": "HealthResponse",
        "type": "object"
      },
      "HealthStatus": {
        "enum": [
          "pass",
          "fail",
          "degraded"
        ],
        "title": "HealthStatus",
        "type": "string"
      },
      "ValidationError": {
        "properties": {
          "ctx": {
            "title": "Context",
            "type": "object"
          },
          "input": {
            "title": "Input"
          },
          "loc": {
            "items": {
              "anyOf": [
                {
                  "type": "string"
                },
                {
                  "type": "integer"
                }
              ]
            },
            "title": "Location",
            "type": "array"
          },
          "msg": {
            "title": "Message",
            "type": "string"
          },
          "type": {
            "title": "Error Type",
            "type": "string"
          }
        },
        "required": [
          "loc",
          "msg",
          "type"
        ],
        "title": "ValidationError",
        "type": "object"
      },
      "connect-protocol-version": {
        "const": 1,
        "description": "Define the version of the Connect protocol",
        "examples": [
          1
        ],
        "title": "Connect-Protocol-Version",
        "type": "number"
      },
      "connect-timeout-header": {
        "description": "Define the timeout, in ms",
        "examples": [
          1000
        ],
        "title": "Connect-Timeout-Ms",
        "type": "number"
      },
      "connect.error": {
        "additionalProperties": true,
        "description": "Error type returned by Connect: https://connectrpc.com/docs/go/errors/#http-representation",
        "properties": {
          "code": {
            "description": "The status code, which should be an enum value of [google.rpc.Code][google.rpc.Code].",
            "enum": [
              "canceled",
              "unknown",
              "invalid_argument",
              "deadline_exceeded",
              "not_found",
              "already_exists",
              "permission_denied",
              "resource_exhausted",
              "failed_precondition",
              "aborted",
              "out_of_range",
              "unimplemented",
              "internal",
              "unavailable",
              "data_loss",
              "unauthenticated"
            ],
            "examples": [
              "not_found"
            ],
            "type": "string"
          },
          "details": {
            "description": "A list of messages that carry the error details. There is no limit on the number of messages.",
            "items": {
              "$ref": "#/components/schemas/connect.error_details.Any"
            },
            "type": "array"
          },
          "message": {
            "description": "A developer-facing error message, which should be in English. Any user-facing error message should be localized and sent in the [google.rpc.Status.details][google.rpc.Status.details] field, or localized by the client.",
            "type": "string"
          }
        },
        "title": "Connect Error",
        "type": "object"
      },
      "connect.error_details.Any": {
        "additionalProperties": true,
        "description": "Contains an arbitrary serialized message along with a @type that describes the type of the serialized message, with an additional debug field for ConnectRPC error details.",
        "properties": {
          "debug": {
            "additionalProperties": true,
            "description": "Deserialized error detail payload. The 'type' field indicates the schema. This field is for easier debugging and should not be relied upon for application logic.",
            "title": "Debug",
            "type": "object"
          },
          "type": {
            "description": "A URL that acts as a globally unique identifier for the type of the serialized message. For example: `type.googleapis.com/google.rpc.ErrorInfo`.",
            "type": "string"
          },
          "value": {
            "description": "The Protobuf message, serialized as bytes and base64-encoded. The specific message type is identified by the `type` field.",
            "format": "byte",
            "type": "string"
          }
        },
        "type": "object"
      },
      "server.v1.HealthCheckRequest": {
        "additionalProperties": false,
        "properties": {
          "checkDependencies": {
            "title": "check_dependencies",
            "type": "boolean"
          },
          "full": {
            "title": "full",
            "type": "boolean"
          }
        },
        "title": "HealthCheckRequest",
        "type": "object"
      },
      "server.v1.HealthCheckResponse": {
        "additionalProperties": false,
        "properties": {
          "dependencies": {
            "additionalProperties": {
              "title": "value",
              "type": "string"
            },
            "description": "Populated only when the request asks for both a full report and dependency checks.",
            "title": "dependencies",
            "type": "object"
          },
          "status": {
            "allOf": [
              {
                "$ref": "#/components/schemas/server.v1.HealthCheckResponse.Status"
              }
            ],
            "title": "status"
          },
          "version": {
            "description": "Set only when the request asks for a full report.",
            "title": "version",
            "type": [
              "string",
              "null"
            ]
          }
        },
        "title": "HealthCheckResponse",
        "type": "object"
      },
      "server.v1.HealthCheckResponse.Status": {
        "enum": [
          "STATUS_UNSPECIFIED",
          "STATUS_PASS",
          "STATUS_FAIL",
          "STATUS_DEGRADED"
        ],
        "title": "Status",
        "type": "string"
      }
    }
  },
  "info": {
    "title": "Armada - Printer Fleet Management",
    "version": "0.1.3"
  },
  "openapi": "3.1.0",
  "paths": {
    "/api/health_check": {
      "get": {
        "operationId": "health_api_health_check_get",
        "parameters": [
          {
            "in": "query",
            "name": "full",
            "required": false,
            "schema": {
              "default": false,
              "title": "Full",
              "type": "boolean"
            }
          },
          {
            "in": "query",
            "name": "check_dependencies",
            "required": false,
            "schema": {
              "default": false,
              "title": "Check Dependencies",
              "type": "boolean"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HealthResponse"
                }
              }
            },
            "description": "Service is healthy or degraded"
          },
          "422": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/HTTPValidationError"
                }
              }
            },
            "description": "Validation Error"
          },
          "503": {
            "description": "Service is unhealthy"
          }
        },
        "summary": "Health",
        "tags": [
          "General"
        ]
      }
    },
    "/api/server.v1.HealthCheckService/HealthCheck": {
      "post": {
        "operationId": "server.v1.HealthCheckService.HealthCheck",
        "parameters": [
          {
            "description": "Define the version of the Connect protocol",
            "example": 1,
            "in": "header",
            "name": "Connect-Protocol-Version",
            "schema": {
              "$ref": "#/components/schemas/connect-protocol-version"
            }
          },
          {
            "description": "Define the timeout, in ms",
            "example": 1000,
            "in": "header",
            "name": "Connect-Timeout-Ms",
            "schema": {
              "$ref": "#/components/schemas/connect-timeout-header"
            }
          }
        ],
        "requestBody": {
          "content": {
            "application/json": {
              "schema": {
                "$ref": "#/components/schemas/server.v1.HealthCheckRequest"
              }
            }
          },
          "required": true
        },
        "responses": {
          "200": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/server.v1.HealthCheckResponse"
                }
              }
            },
            "description": "Success"
          },
          "default": {
            "content": {
              "application/json": {
                "schema": {
                  "$ref": "#/components/schemas/connect.error"
                }
              }
            },
            "description": "Error"
          }
        },
        "summary": "HealthCheck",
        "tags": [
          "server.v1.HealthCheckService"
        ]
      }
    }
  },
  "tags": [
    {
      "name": "server.v1.HealthCheckService"
    }
  ]
};
