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
      "common.v1.PageRequest": {
        "additionalProperties": false,
        "description": "Asks for one page of a list. Every List RPC request carries this as its page field.",
        "properties": {
          "pageSize": {
            "description": "How many items to return. The server applies a default when unset and caps large values.",
            "title": "page_size",
            "type": "integer"
          },
          "pageToken": {
            "description": "Where to continue from: the previous response's next_page_token. Empty for the first page.\n Opaque; never parse or build one.",
            "title": "page_token",
            "type": "string"
          }
        },
        "title": "PageRequest",
        "type": "object"
      },
      "common.v1.PageResponse": {
        "additionalProperties": false,
        "description": "Describes the page returned. Every List RPC response carries this as its page field.",
        "properties": {
          "nextPageToken": {
            "description": "Pass as page_token to get the next page. Empty when this is the last page.",
            "title": "next_page_token",
            "type": "string"
          }
        },
        "title": "PageResponse",
        "type": "object"
      },
      "common.v1.TimeStatus": {
        "additionalProperties": false,
        "description": "The base timestamps every entity carries, in UTC. A lifecycle need beyond these, such as\n soft delete, uses a superset message that nests this one.",
        "properties": {
          "createdAt": {
            "allOf": [
              {
                "$ref": "#/components/schemas/google.protobuf.Timestamp"
              }
            ],
            "description": "When the entity was created.",
            "title": "created_at"
          },
          "updatedAt": {
            "allOf": [
              {
                "$ref": "#/components/schemas/google.protobuf.Timestamp"
              }
            ],
            "description": "When the entity last changed or, for observed state, was last observed.",
            "title": "updated_at"
          }
        },
        "title": "TimeStatus",
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
      "file.v1.File": {
        "additionalProperties": false,
        "description": "A file held in file storage. Its storage location is server-internal and never sent.",
        "properties": {
          "fileType": {
            "allOf": [
              {
                "$ref": "#/components/schemas/file.v1.FileType"
              }
            ],
            "description": "The file's format.",
            "title": "file_type"
          },
          "filename": {
            "description": "The name the uploader gave it. Display only.",
            "title": "filename",
            "type": "string"
          },
          "id": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.FileId"
              }
            ],
            "description": "This file.",
            "title": "id"
          },
          "sha256": {
            "description": "Lower-case hex SHA-256 of the stored bytes, for integrity checks.",
            "title": "sha256",
            "type": "string"
          },
          "sizeBytes": {
            "description": "Size of the stored bytes.",
            "format": "int64",
            "title": "size_bytes",
            "type": "string"
          },
          "timeStatus": {
            "allOf": [
              {
                "$ref": "#/components/schemas/common.v1.TimeStatus"
              }
            ],
            "description": "When the file was created and last changed.",
            "title": "time_status"
          }
        },
        "title": "File",
        "type": "object"
      },
      "file.v1.FileType": {
        "description": "The format of a stored file. Names stay vendor-neutral so any printer brand fits.",
        "enum": [
          "FILE_TYPE_UNSPECIFIED",
          "FILE_TYPE_GCODE",
          "FILE_TYPE_CGCODE"
        ],
        "title": "FileType",
        "type": "string"
      },
      "file.v1.FileUploadMetadata": {
        "additionalProperties": false,
        "description": "Upload pair, call 1 of 2: what the client is about to upload. Every domain that accepts\n large files takes this in its own Create<Thing>Upload request, alongside the ID of the\n entity the file belongs to.",
        "properties": {
          "fileType": {
            "allOf": [
              {
                "$ref": "#/components/schemas/file.v1.FileType"
              }
            ],
            "description": "The file's format.",
            "title": "file_type"
          },
          "filename": {
            "description": "The file's name on the client. Display only.",
            "title": "filename",
            "type": "string"
          },
          "sha256": {
            "description": "Lower-case hex SHA-256 of those bytes. The server rejects an upload that does not match.",
            "title": "sha256",
            "type": "string"
          },
          "sizeBytes": {
            "description": "Exact size of the bytes that will be sent.",
            "format": "int64",
            "title": "size_bytes",
            "type": "string"
          }
        },
        "title": "FileUploadMetadata",
        "type": "object"
      },
      "file.v1.FileUploadSlot": {
        "additionalProperties": false,
        "description": "Where to send the bytes. Upload pair, call 2 of 2, is an HTTP PUT of the raw file bytes to\n upload_url. The slot expires a server-configured time after the file's\n time_status.updated_at.",
        "properties": {
          "fileId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.FileId"
              }
            ],
            "description": "The file the bytes will become, already linked to its owning entity.",
            "title": "file_id"
          },
          "uploadUrl": {
            "description": "Where to PUT the bytes. Treat it as an opaque, short-lived credential.",
            "title": "upload_url",
            "type": "string"
          }
        },
        "title": "FileUploadSlot",
        "type": "object"
      },
      "google.protobuf.Timestamp": {
        "description": "A point in time in RFC 3339 format, with up to nanosecond precision. Output uses UTC (`Z`); input may use an offset from UTC.",
        "examples": [
          "2023-01-15T01:30:15.01Z",
          "2024-12-25T12:00:00Z"
        ],
        "format": "date-time",
        "type": "string"
      },
      "id.v1.FileId": {
        "additionalProperties": false,
        "description": "Identifies a file.v1.File.",
        "properties": {
          "value": {
            "description": "UUID.",
            "title": "value",
            "type": "string"
          }
        },
        "title": "FileId",
        "type": "object"
      },
      "id.v1.PrintJobId": {
        "additionalProperties": false,
        "description": "Identifies a print_job.v1.PrintJob.",
        "properties": {
          "value": {
            "description": "UUID.",
            "title": "value",
            "type": "string"
          }
        },
        "title": "PrintJobId",
        "type": "object"
      },
      "id.v1.PrinterId": {
        "additionalProperties": false,
        "description": "Identifies a printer.v1.Printer.",
        "properties": {
          "value": {
            "description": "UUID.",
            "title": "value",
            "type": "string"
          }
        },
        "title": "PrinterId",
        "type": "object"
      },
      "id.v1.PrinterQueueId": {
        "additionalProperties": false,
        "description": "Identifies a printer_queue.v1.PrinterQueue.",
        "properties": {
          "value": {
            "description": "UUID.",
            "title": "value",
            "type": "string"
          }
        },
        "title": "PrinterQueueId",
        "type": "object"
      },
      "id.v1.UserId": {
        "additionalProperties": false,
        "description": "Identifies a user.",
        "properties": {
          "value": {
            "description": "UUID.",
            "title": "value",
            "type": "string"
          }
        },
        "title": "UserId",
        "type": "object"
      },
      "print_job.v1.PrintJob": {
        "additionalProperties": false,
        "description": "A request to print one file. It is created first, as a DRAFT, and its file is attached to it.",
        "properties": {
          "fileId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.FileId"
              }
            ],
            "description": "The file to print. Unset until an upload is created for the job.",
            "title": "file_id"
          },
          "id": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrintJobId"
              }
            ],
            "description": "This job.",
            "title": "id"
          },
          "printerId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrinterId"
              }
            ],
            "description": "The printer it is assigned to. Unset until assigned.",
            "title": "printer_id"
          },
          "printerQueueId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrinterQueueId"
              }
            ],
            "description": "The queue the server placed it in on submission. Staff may move it; students never choose it.",
            "title": "printer_queue_id"
          },
          "status": {
            "allOf": [
              {
                "$ref": "#/components/schemas/print_job.v1.PrintJobStatus"
              }
            ],
            "description": "Current status.",
            "title": "status"
          },
          "statusReason": {
            "description": "Why the job was rejected, failed or cancelled. Visible to the student.",
            "title": "status_reason",
            "type": [
              "string",
              "null"
            ]
          },
          "timeStatus": {
            "allOf": [
              {
                "$ref": "#/components/schemas/common.v1.TimeStatus"
              }
            ],
            "description": "When the job was created and last changed.",
            "title": "time_status"
          },
          "userId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.UserId"
              }
            ],
            "description": "The user who created it.",
            "title": "user_id"
          },
          "userNotes": {
            "description": "Notes the submitting user wrote.",
            "title": "user_notes",
            "type": "string"
          }
        },
        "title": "PrintJob",
        "type": "object"
      },
      "print_job.v1.PrintJobStatus": {
        "description": "Where a print job is in its life. The server alone decides transitions.",
        "enum": [
          "PRINT_JOB_STATUS_UNSPECIFIED",
          "PRINT_JOB_STATUS_DRAFT",
          "PRINT_JOB_STATUS_SUBMITTED",
          "PRINT_JOB_STATUS_UNDER_REVIEW",
          "PRINT_JOB_STATUS_APPROVED",
          "PRINT_JOB_STATUS_REJECTED",
          "PRINT_JOB_STATUS_ASSIGNED",
          "PRINT_JOB_STATUS_PRINTING",
          "PRINT_JOB_STATUS_FINISHED",
          "PRINT_JOB_STATUS_COMPLETED",
          "PRINT_JOB_STATUS_FAILED",
          "PRINT_JOB_STATUS_CANCELLED"
        ],
        "title": "PrintJobStatus",
        "type": "string"
      },
      "printer.v1.Printer": {
        "additionalProperties": false,
        "description": "A physical printer.",
        "properties": {
          "id": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrinterId"
              }
            ],
            "description": "This printer.",
            "title": "id"
          },
          "model": {
            "description": "The printer's model.",
            "title": "model",
            "type": "string"
          },
          "name": {
            "description": "Display name, stable across restarts.",
            "title": "name",
            "type": "string"
          },
          "printJobId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrintJobId"
              }
            ],
            "description": "The job it is running. Unset when idle.",
            "title": "print_job_id"
          },
          "progressPercent": {
            "description": "Progress of the current job, 0 to 100, when the printer reports it.",
            "title": "progress_percent",
            "type": [
              "integer",
              "null"
            ]
          },
          "status": {
            "allOf": [
              {
                "$ref": "#/components/schemas/printer.v1.PrinterStatus"
              }
            ],
            "description": "Latest observed status.",
            "title": "status"
          },
          "timeStatus": {
            "allOf": [
              {
                "$ref": "#/components/schemas/common.v1.TimeStatus"
              }
            ],
            "description": "When the printer was added. updated_at is when its status was last observed, which\n clients use to show stale data.",
            "title": "time_status"
          }
        },
        "title": "Printer",
        "type": "object"
      },
      "printer.v1.PrinterStatus": {
        "description": "A printer's normalized state. Adapters map each vendor's states onto these.",
        "enum": [
          "PRINTER_STATUS_UNSPECIFIED",
          "PRINTER_STATUS_OFFLINE",
          "PRINTER_STATUS_IDLE",
          "PRINTER_STATUS_PRINTING",
          "PRINTER_STATUS_FINISHED",
          "PRINTER_STATUS_ERROR"
        ],
        "title": "PrinterStatus",
        "type": "string"
      },
      "printer_queue.v1.PrinterQueue": {
        "additionalProperties": false,
        "description": "A line of print jobs waiting for a printer.",
        "properties": {
          "id": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrinterQueueId"
              }
            ],
            "description": "This queue.",
            "title": "id"
          },
          "isActive": {
            "description": "Whether it accepts new jobs.",
            "title": "is_active",
            "type": "boolean"
          },
          "name": {
            "description": "Display name.",
            "title": "name",
            "type": "string"
          },
          "timeStatus": {
            "allOf": [
              {
                "$ref": "#/components/schemas/common.v1.TimeStatus"
              }
            ],
            "description": "When the queue was created and last changed.",
            "title": "time_status"
          }
        },
        "title": "PrinterQueue",
        "type": "object"
      },
      "server.v1.CreatePrintJobRequest": {
        "additionalProperties": false,
        "description": "Creates a DRAFT job.",
        "properties": {
          "userNotes": {
            "description": "Notes for staff.",
            "title": "user_notes",
            "type": "string"
          }
        },
        "title": "CreatePrintJobRequest",
        "type": "object"
      },
      "server.v1.CreatePrintJobResponse": {
        "additionalProperties": false,
        "description": "The new job.",
        "properties": {
          "printJob": {
            "allOf": [
              {
                "$ref": "#/components/schemas/print_job.v1.PrintJob"
              }
            ],
            "description": "The job, in DRAFT with no file yet.",
            "title": "print_job"
          }
        },
        "title": "CreatePrintJobResponse",
        "type": "object"
      },
      "server.v1.CreatePrintJobUploadRequest": {
        "additionalProperties": false,
        "description": "Describes the print file about to be uploaded for a job.",
        "properties": {
          "metadata": {
            "allOf": [
              {
                "$ref": "#/components/schemas/file.v1.FileUploadMetadata"
              }
            ],
            "description": "The file to be uploaded.",
            "title": "metadata"
          },
          "printJobId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrintJobId"
              }
            ],
            "description": "The DRAFT job the file belongs to.",
            "title": "print_job_id"
          }
        },
        "title": "CreatePrintJobUploadRequest",
        "type": "object"
      },
      "server.v1.CreatePrintJobUploadResponse": {
        "additionalProperties": false,
        "description": "Where to upload the job's print file.",
        "properties": {
          "slot": {
            "allOf": [
              {
                "$ref": "#/components/schemas/file.v1.FileUploadSlot"
              }
            ],
            "description": "The upload slot. Its file_id is now the job's file_id.",
            "title": "slot"
          }
        },
        "title": "CreatePrintJobUploadResponse",
        "type": "object"
      },
      "server.v1.GetFileRequest": {
        "additionalProperties": false,
        "description": "Gets one file.",
        "properties": {
          "fileId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.FileId"
              }
            ],
            "description": "The file to get.",
            "title": "file_id"
          }
        },
        "title": "GetFileRequest",
        "type": "object"
      },
      "server.v1.GetFileResponse": {
        "additionalProperties": false,
        "description": "One file.",
        "properties": {
          "file": {
            "allOf": [
              {
                "$ref": "#/components/schemas/file.v1.File"
              }
            ],
            "description": "The file.",
            "title": "file"
          }
        },
        "title": "GetFileResponse",
        "type": "object"
      },
      "server.v1.GetPrintJobRequest": {
        "additionalProperties": false,
        "description": "Gets one print job.",
        "properties": {
          "printJobId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrintJobId"
              }
            ],
            "description": "The job to get.",
            "title": "print_job_id"
          }
        },
        "title": "GetPrintJobRequest",
        "type": "object"
      },
      "server.v1.GetPrintJobResponse": {
        "additionalProperties": false,
        "description": "One job and its file.",
        "properties": {
          "file": {
            "allOf": [
              {
                "$ref": "#/components/schemas/file.v1.File"
              }
            ],
            "description": "The job's file. Unset while a DRAFT job has no upload.",
            "title": "file"
          },
          "printJob": {
            "allOf": [
              {
                "$ref": "#/components/schemas/print_job.v1.PrintJob"
              }
            ],
            "description": "The job.",
            "title": "print_job"
          }
        },
        "title": "GetPrintJobResponse",
        "type": "object"
      },
      "server.v1.GetPrinterQueueRequest": {
        "additionalProperties": false,
        "description": "Gets one queue.",
        "properties": {
          "printerQueueId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrinterQueueId"
              }
            ],
            "description": "The queue to get.",
            "title": "printer_queue_id"
          }
        },
        "title": "GetPrinterQueueRequest",
        "type": "object"
      },
      "server.v1.GetPrinterQueueResponse": {
        "additionalProperties": false,
        "description": "One queue.",
        "properties": {
          "printerQueue": {
            "allOf": [
              {
                "$ref": "#/components/schemas/printer_queue.v1.PrinterQueue"
              }
            ],
            "description": "The queue.",
            "title": "printer_queue"
          }
        },
        "title": "GetPrinterQueueResponse",
        "type": "object"
      },
      "server.v1.GetPrinterRequest": {
        "additionalProperties": false,
        "description": "Gets one printer.",
        "properties": {
          "printerId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrinterId"
              }
            ],
            "description": "The printer to get.",
            "title": "printer_id"
          }
        },
        "title": "GetPrinterRequest",
        "type": "object"
      },
      "server.v1.GetPrinterResponse": {
        "additionalProperties": false,
        "description": "One printer.",
        "properties": {
          "printer": {
            "allOf": [
              {
                "$ref": "#/components/schemas/printer.v1.Printer"
              }
            ],
            "description": "The printer as the printer server reports it.",
            "title": "printer"
          }
        },
        "title": "GetPrinterResponse",
        "type": "object"
      },
      "server.v1.HealthCheckRequest": {
        "additionalProperties": false,
        "description": "Asks how healthy the server is.",
        "properties": {
          "checkDependencies": {
            "description": "Probe dependencies such as the database. Slower than a plain liveness check.",
            "title": "check_dependencies",
            "type": "boolean"
          },
          "full": {
            "description": "Include the version, and dependency results when they are checked.",
            "title": "full",
            "type": "boolean"
          }
        },
        "title": "HealthCheckRequest",
        "type": "object"
      },
      "server.v1.HealthCheckResponse": {
        "additionalProperties": false,
        "description": "The server's health.",
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
            "description": "Overall health.",
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
        "description": "Overall health.",
        "enum": [
          "STATUS_UNSPECIFIED",
          "STATUS_PASS",
          "STATUS_FAIL",
          "STATUS_DEGRADED"
        ],
        "title": "Status",
        "type": "string"
      },
      "server.v1.ListFilesRequest": {
        "additionalProperties": false,
        "description": "Gets several files.",
        "properties": {
          "fileIds": {
            "description": "The files to get.",
            "items": {
              "$ref": "#/components/schemas/id.v1.FileId"
            },
            "title": "file_ids",
            "type": "array"
          }
        },
        "title": "ListFilesRequest",
        "type": "object"
      },
      "server.v1.ListFilesResponse": {
        "additionalProperties": false,
        "description": "The files that were found.",
        "properties": {
          "files": {
            "description": "The files. An unknown ID is left out.",
            "items": {
              "$ref": "#/components/schemas/file.v1.File"
            },
            "title": "files",
            "type": "array"
          }
        },
        "title": "ListFilesResponse",
        "type": "object"
      },
      "server.v1.ListPrintJobsRequest": {
        "additionalProperties": false,
        "description": "Lists print jobs.",
        "properties": {
          "page": {
            "allOf": [
              {
                "$ref": "#/components/schemas/common.v1.PageRequest"
              }
            ],
            "description": "Which page to return.",
            "title": "page"
          }
        },
        "title": "ListPrintJobsRequest",
        "type": "object"
      },
      "server.v1.ListPrintJobsResponse": {
        "additionalProperties": false,
        "description": "One page of jobs and their files.",
        "properties": {
          "files": {
            "description": "The files the jobs refer to, matched by file_id.",
            "items": {
              "$ref": "#/components/schemas/file.v1.File"
            },
            "title": "files",
            "type": "array"
          },
          "page": {
            "allOf": [
              {
                "$ref": "#/components/schemas/common.v1.PageResponse"
              }
            ],
            "description": "How to get the next page.",
            "title": "page"
          },
          "printJobs": {
            "description": "The jobs.",
            "items": {
              "$ref": "#/components/schemas/print_job.v1.PrintJob"
            },
            "title": "print_jobs",
            "type": "array"
          }
        },
        "title": "ListPrintJobsResponse",
        "type": "object"
      },
      "server.v1.ListPrinterQueuesRequest": {
        "additionalProperties": false,
        "description": "Lists queues.",
        "properties": {
          "page": {
            "allOf": [
              {
                "$ref": "#/components/schemas/common.v1.PageRequest"
              }
            ],
            "description": "Which page to return.",
            "title": "page"
          }
        },
        "title": "ListPrinterQueuesRequest",
        "type": "object"
      },
      "server.v1.ListPrinterQueuesResponse": {
        "additionalProperties": false,
        "description": "The queues returned for the requested page, and the token for the page after it.",
        "properties": {
          "page": {
            "allOf": [
              {
                "$ref": "#/components/schemas/common.v1.PageResponse"
              }
            ],
            "description": "How to get the next page.",
            "title": "page"
          },
          "printerQueues": {
            "description": "The queues.",
            "items": {
              "$ref": "#/components/schemas/printer_queue.v1.PrinterQueue"
            },
            "title": "printer_queues",
            "type": "array"
          }
        },
        "title": "ListPrinterQueuesResponse",
        "type": "object"
      },
      "server.v1.ListPrintersRequest": {
        "additionalProperties": false,
        "description": "Lists printers.",
        "properties": {
          "page": {
            "allOf": [
              {
                "$ref": "#/components/schemas/common.v1.PageRequest"
              }
            ],
            "description": "Which page to return.",
            "title": "page"
          }
        },
        "title": "ListPrintersRequest",
        "type": "object"
      },
      "server.v1.ListPrintersResponse": {
        "additionalProperties": false,
        "description": "One page of printers.",
        "properties": {
          "page": {
            "allOf": [
              {
                "$ref": "#/components/schemas/common.v1.PageResponse"
              }
            ],
            "description": "How to get the next page.",
            "title": "page"
          },
          "printers": {
            "description": "The printers.",
            "items": {
              "$ref": "#/components/schemas/printer.v1.Printer"
            },
            "title": "printers",
            "type": "array"
          }
        },
        "title": "ListPrintersResponse",
        "type": "object"
      },
      "server.v1.SubmitPrintJobRequest": {
        "additionalProperties": false,
        "description": "Submits a DRAFT job.",
        "properties": {
          "printJobId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrintJobId"
              }
            ],
            "description": "The job to submit. Its file must have finished uploading.",
            "title": "print_job_id"
          }
        },
        "title": "SubmitPrintJobRequest",
        "type": "object"
      },
      "server.v1.SubmitPrintJobResponse": {
        "additionalProperties": false,
        "description": "The submitted job.",
        "properties": {
          "file": {
            "allOf": [
              {
                "$ref": "#/components/schemas/file.v1.File"
              }
            ],
            "description": "The job's file.",
            "title": "file"
          },
          "printJob": {
            "allOf": [
              {
                "$ref": "#/components/schemas/print_job.v1.PrintJob"
              }
            ],
            "description": "The job, now SUBMITTED.",
            "title": "print_job"
          }
        },
        "title": "SubmitPrintJobResponse",
        "type": "object"
      },
      "server.v1.TransitionPrintJobRequest": {
        "anyOf": [
          {
            "properties": {
              "approve": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/server.v1.TransitionPrintJobRequest.Approve"
                  }
                ],
                "description": "Approve.",
                "title": "approve"
              }
            },
            "title": "approve",
            "type": "object"
          },
          {
            "properties": {
              "assign": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/server.v1.TransitionPrintJobRequest.Assign"
                  }
                ],
                "description": "Assign to a printer.",
                "title": "assign"
              }
            },
            "title": "assign",
            "type": "object"
          },
          {
            "properties": {
              "complete": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/server.v1.TransitionPrintJobRequest.Complete"
                  }
                ],
                "description": "Confirm the finished print.",
                "title": "complete"
              }
            },
            "title": "complete",
            "type": "object"
          },
          {
            "properties": {
              "fail": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/server.v1.TransitionPrintJobRequest.Fail"
                  }
                ],
                "description": "Mark the print failed with a reason.",
                "title": "fail"
              }
            },
            "title": "fail",
            "type": "object"
          },
          {
            "properties": {
              "moveToQueue": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/server.v1.TransitionPrintJobRequest.MoveToQueue"
                  }
                ],
                "description": "Move to another queue.",
                "title": "move_to_queue"
              }
            },
            "title": "move_to_queue",
            "type": "object"
          },
          {
            "properties": {
              "reject": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/server.v1.TransitionPrintJobRequest.Reject"
                  }
                ],
                "description": "Reject with a reason.",
                "title": "reject"
              }
            },
            "title": "reject",
            "type": "object"
          },
          {
            "properties": {
              "startReview": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/server.v1.TransitionPrintJobRequest.StartReview"
                  }
                ],
                "description": "Start reviewing.",
                "title": "start_review"
              }
            },
            "title": "start_review",
            "type": "object"
          }
        ],
        "description": "Changes a job's status through one staff action.",
        "not": {
          "allOf": [
            {
              "anyOf": [
                {
                  "required": [
                    "approve"
                  ]
                },
                {
                  "required": [
                    "assign"
                  ]
                },
                {
                  "required": [
                    "complete"
                  ]
                },
                {
                  "required": [
                    "fail"
                  ]
                },
                {
                  "required": [
                    "moveToQueue"
                  ]
                },
                {
                  "required": [
                    "reject"
                  ]
                },
                {
                  "required": [
                    "startReview"
                  ]
                }
              ]
            },
            {
              "not": {
                "oneOf": [
                  {
                    "required": [
                      "approve"
                    ]
                  },
                  {
                    "required": [
                      "assign"
                    ]
                  },
                  {
                    "required": [
                      "complete"
                    ]
                  },
                  {
                    "required": [
                      "fail"
                    ]
                  },
                  {
                    "required": [
                      "moveToQueue"
                    ]
                  },
                  {
                    "required": [
                      "reject"
                    ]
                  },
                  {
                    "required": [
                      "startReview"
                    ]
                  }
                ]
              }
            }
          ]
        },
        "properties": {
          "printJobId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrintJobId"
              }
            ],
            "description": "The job to change.",
            "title": "print_job_id"
          }
        },
        "title": "TransitionPrintJobRequest",
        "type": "object",
        "unevaluatedProperties": false
      },
      "server.v1.TransitionPrintJobRequest.Approve": {
        "additionalProperties": false,
        "description": "Approves a job UNDER_REVIEW, moving it to APPROVED.",
        "title": "Approve",
        "type": "object"
      },
      "server.v1.TransitionPrintJobRequest.Assign": {
        "additionalProperties": false,
        "description": "Dispatches an APPROVED job to an idle printer, moving it to ASSIGNED. The server moves it\n to PRINTING once the printer reports the print started.",
        "properties": {
          "printerId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrinterId"
              }
            ],
            "description": "The printer to print it on.",
            "title": "printer_id"
          }
        },
        "title": "Assign",
        "type": "object"
      },
      "server.v1.TransitionPrintJobRequest.Complete": {
        "additionalProperties": false,
        "description": "Staff checked the print of a FINISHED job and accept it, moving it to COMPLETED.",
        "title": "Complete",
        "type": "object"
      },
      "server.v1.TransitionPrintJobRequest.Fail": {
        "additionalProperties": false,
        "description": "Staff mark an ASSIGNED, PRINTING or FINISHED job's print failed, moving it to FAILED. The\n printer is left as it is; an operator readies it separately.",
        "properties": {
          "reason": {
            "description": "Why, shown to the student. Required.",
            "title": "reason",
            "type": "string"
          }
        },
        "title": "Fail",
        "type": "object"
      },
      "server.v1.TransitionPrintJobRequest.MoveToQueue": {
        "additionalProperties": false,
        "description": "Moves a job that is not yet assigned to another queue.",
        "properties": {
          "printerQueueId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrinterQueueId"
              }
            ],
            "description": "The queue to move it to.",
            "title": "printer_queue_id"
          }
        },
        "title": "MoveToQueue",
        "type": "object"
      },
      "server.v1.TransitionPrintJobRequest.Reject": {
        "additionalProperties": false,
        "description": "Rejects a job UNDER_REVIEW, moving it to REJECTED.",
        "properties": {
          "reason": {
            "description": "Why, shown to the student. Required.",
            "title": "reason",
            "type": "string"
          }
        },
        "title": "Reject",
        "type": "object"
      },
      "server.v1.TransitionPrintJobRequest.StartReview": {
        "additionalProperties": false,
        "description": "Opens a SUBMITTED job for review, moving it to UNDER_REVIEW.",
        "title": "StartReview",
        "type": "object"
      },
      "server.v1.TransitionPrintJobResponse": {
        "additionalProperties": false,
        "description": "The job after the change.",
        "properties": {
          "printJob": {
            "allOf": [
              {
                "$ref": "#/components/schemas/print_job.v1.PrintJob"
              }
            ],
            "description": "The job with its new status.",
            "title": "print_job"
          }
        },
        "title": "TransitionPrintJobResponse",
        "type": "object"
      },
      "server.v1.TransitionPrinterRequest": {
        "anyOf": [
          {
            "properties": {
              "ready": {
                "allOf": [
                  {
                    "$ref": "#/components/schemas/server.v1.TransitionPrinterRequest.Ready"
                  }
                ],
                "description": "Mark ready for the next job.",
                "title": "ready"
              }
            },
            "title": "ready",
            "type": "object"
          }
        ],
        "description": "Changes a printer's state through one operator action.",
        "properties": {
          "printerId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.PrinterId"
              }
            ],
            "description": "The printer to change.",
            "title": "printer_id"
          }
        },
        "title": "TransitionPrinterRequest",
        "type": "object",
        "unevaluatedProperties": false
      },
      "server.v1.TransitionPrinterRequest.Ready": {
        "additionalProperties": false,
        "description": "The operator cleared a FINISHED or ERROR printer, so it is IDLE and ready for its next job.",
        "title": "Ready",
        "type": "object"
      },
      "server.v1.TransitionPrinterResponse": {
        "additionalProperties": false,
        "description": "The printer after the change.",
        "properties": {
          "printer": {
            "allOf": [
              {
                "$ref": "#/components/schemas/printer.v1.Printer"
              }
            ],
            "description": "The printer as the printer server reports it.",
            "title": "printer"
          }
        },
        "title": "TransitionPrinterResponse",
        "type": "object"
      }
    }
  },
  "info": {
    "title": "Armada - Printer Fleet Management",
    "version": "0.1.5"
  },
  "openapi": "3.1.0",
  "paths": {
    "/api/files/{file_id}": {
      "delete": {
        "operationId": "delete_file_api_files__file_id__delete",
        "parameters": [
          {
            "in": "path",
            "name": "file_id",
            "required": true,
            "schema": {
              "format": "uuid",
              "title": "File Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "204": {
            "description": "Successful Response"
          },
          "404": {
            "description": "No such file, or its bytes are missing"
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
            "description": "File storage is unavailable"
          }
        },
        "summary": "Delete File",
        "tags": [
          "Files"
        ]
      },
      "get": {
        "operationId": "download_file_api_files__file_id__get",
        "parameters": [
          {
            "in": "path",
            "name": "file_id",
            "required": true,
            "schema": {
              "format": "uuid",
              "title": "File Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "200": {
            "content": {
              "application/octet-stream": {}
            },
            "description": "Successful Response"
          },
          "404": {
            "description": "No such file, or its bytes are missing"
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
            "description": "File storage is unavailable"
          }
        },
        "summary": "Download File",
        "tags": [
          "Files"
        ]
      },
      "put": {
        "description": "Upload pair, call 2 of 2: the raw bytes of a file created by a Create...Upload RPC.",
        "operationId": "upload_file_api_files__file_id__put",
        "parameters": [
          {
            "in": "path",
            "name": "file_id",
            "required": true,
            "schema": {
              "format": "uuid",
              "title": "File Id",
              "type": "string"
            }
          }
        ],
        "responses": {
          "204": {
            "description": "Successful Response"
          },
          "400": {
            "description": "The bytes do not match the file"
          },
          "404": {
            "description": "No such file, or its bytes are missing"
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
            "description": "File storage is unavailable"
          }
        },
        "summary": "Upload File",
        "tags": [
          "Files"
        ]
      }
    },
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
    "/api/server.v1.FileService/GetFile": {
      "post": {
        "description": "Gets one file.",
        "operationId": "server.v1.FileService.GetFile",
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
                "$ref": "#/components/schemas/server.v1.GetFileRequest"
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
                  "$ref": "#/components/schemas/server.v1.GetFileResponse"
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
        "summary": "GetFile",
        "tags": [
          "server.v1.FileService"
        ]
      }
    },
    "/api/server.v1.FileService/ListFiles": {
      "post": {
        "description": "Gets several files by ID.",
        "operationId": "server.v1.FileService.ListFiles",
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
                "$ref": "#/components/schemas/server.v1.ListFilesRequest"
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
                  "$ref": "#/components/schemas/server.v1.ListFilesResponse"
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
        "summary": "ListFiles",
        "tags": [
          "server.v1.FileService"
        ]
      }
    },
    "/api/server.v1.HealthCheckService/HealthCheck": {
      "post": {
        "description": "Reports the server's health.",
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
    },
    "/api/server.v1.PrintJobService/CreatePrintJob": {
      "post": {
        "description": "Step 1. Creates a DRAFT job to attach a file to.",
        "operationId": "server.v1.PrintJobService.CreatePrintJob",
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
                "$ref": "#/components/schemas/server.v1.CreatePrintJobRequest"
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
                  "$ref": "#/components/schemas/server.v1.CreatePrintJobResponse"
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
        "summary": "CreatePrintJob",
        "tags": [
          "server.v1.PrintJobService"
        ]
      }
    },
    "/api/server.v1.PrintJobService/CreatePrintJobUpload": {
      "post": {
        "description": "Step 2, and upload pair call 1 of 2. Creates the job's file record, links it to the job,\n and returns where to PUT the bytes (call 2 of 2). Calling it again replaces the file.",
        "operationId": "server.v1.PrintJobService.CreatePrintJobUpload",
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
                "$ref": "#/components/schemas/server.v1.CreatePrintJobUploadRequest"
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
                  "$ref": "#/components/schemas/server.v1.CreatePrintJobUploadResponse"
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
        "summary": "CreatePrintJobUpload",
        "tags": [
          "server.v1.PrintJobService"
        ]
      }
    },
    "/api/server.v1.PrintJobService/GetPrintJob": {
      "post": {
        "description": "Gets one print job with its file.",
        "operationId": "server.v1.PrintJobService.GetPrintJob",
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
                "$ref": "#/components/schemas/server.v1.GetPrintJobRequest"
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
                  "$ref": "#/components/schemas/server.v1.GetPrintJobResponse"
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
        "summary": "GetPrintJob",
        "tags": [
          "server.v1.PrintJobService"
        ]
      }
    },
    "/api/server.v1.PrintJobService/ListPrintJobs": {
      "post": {
        "description": "Lists print jobs with their files, one page at a time.",
        "operationId": "server.v1.PrintJobService.ListPrintJobs",
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
                "$ref": "#/components/schemas/server.v1.ListPrintJobsRequest"
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
                  "$ref": "#/components/schemas/server.v1.ListPrintJobsResponse"
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
        "summary": "ListPrintJobs",
        "tags": [
          "server.v1.PrintJobService"
        ]
      }
    },
    "/api/server.v1.PrintJobService/SubmitPrintJob": {
      "post": {
        "description": "Step 3. Submits a DRAFT job whose file has finished uploading, moving it to SUBMITTED. The\n server places it in a queue.",
        "operationId": "server.v1.PrintJobService.SubmitPrintJob",
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
                "$ref": "#/components/schemas/server.v1.SubmitPrintJobRequest"
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
                  "$ref": "#/components/schemas/server.v1.SubmitPrintJobResponse"
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
        "summary": "SubmitPrintJob",
        "tags": [
          "server.v1.PrintJobService"
        ]
      }
    },
    "/api/server.v1.PrintJobService/TransitionPrintJob": {
      "post": {
        "description": "Staff move a job to its next status. Each action carries exactly the fields it needs; the\n server rejects an action that is not valid from the job's current status.",
        "operationId": "server.v1.PrintJobService.TransitionPrintJob",
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
                "$ref": "#/components/schemas/server.v1.TransitionPrintJobRequest"
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
                  "$ref": "#/components/schemas/server.v1.TransitionPrintJobResponse"
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
        "summary": "TransitionPrintJob",
        "tags": [
          "server.v1.PrintJobService"
        ]
      }
    },
    "/api/server.v1.PrinterQueueService/GetPrinterQueue": {
      "post": {
        "description": "Gets one queue.",
        "operationId": "server.v1.PrinterQueueService.GetPrinterQueue",
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
                "$ref": "#/components/schemas/server.v1.GetPrinterQueueRequest"
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
                  "$ref": "#/components/schemas/server.v1.GetPrinterQueueResponse"
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
        "summary": "GetPrinterQueue",
        "tags": [
          "server.v1.PrinterQueueService"
        ]
      }
    },
    "/api/server.v1.PrinterQueueService/ListPrinterQueues": {
      "post": {
        "description": "Lists queues, one page at a time.",
        "operationId": "server.v1.PrinterQueueService.ListPrinterQueues",
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
                "$ref": "#/components/schemas/server.v1.ListPrinterQueuesRequest"
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
                  "$ref": "#/components/schemas/server.v1.ListPrinterQueuesResponse"
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
        "summary": "ListPrinterQueues",
        "tags": [
          "server.v1.PrinterQueueService"
        ]
      }
    },
    "/api/server.v1.PrinterService/GetPrinter": {
      "post": {
        "description": "Gets one printer.",
        "operationId": "server.v1.PrinterService.GetPrinter",
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
                "$ref": "#/components/schemas/server.v1.GetPrinterRequest"
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
                  "$ref": "#/components/schemas/server.v1.GetPrinterResponse"
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
        "summary": "GetPrinter",
        "tags": [
          "server.v1.PrinterService"
        ]
      }
    },
    "/api/server.v1.PrinterService/ListPrinters": {
      "post": {
        "description": "Lists printers, one page at a time.",
        "operationId": "server.v1.PrinterService.ListPrinters",
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
                "$ref": "#/components/schemas/server.v1.ListPrintersRequest"
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
                  "$ref": "#/components/schemas/server.v1.ListPrintersResponse"
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
        "summary": "ListPrinters",
        "tags": [
          "server.v1.PrinterService"
        ]
      }
    },
    "/api/server.v1.PrinterService/TransitionPrinter": {
      "post": {
        "description": "An operator changes a printer's state. The server asks the printer server, and rejects an\n action that is not valid from the printer's current status.",
        "operationId": "server.v1.PrinterService.TransitionPrinter",
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
                "$ref": "#/components/schemas/server.v1.TransitionPrinterRequest"
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
                  "$ref": "#/components/schemas/server.v1.TransitionPrinterResponse"
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
        "summary": "TransitionPrinter",
        "tags": [
          "server.v1.PrinterService"
        ]
      }
    }
  },
  "tags": [
    {
      "description": "File records, served by the remote server. The bytes are never sent through this service.",
      "name": "server.v1.FileService"
    },
    {
      "description": "Reports server health, for monitoring and deployment checks.",
      "name": "server.v1.HealthCheckService"
    },
    {
      "description": "Print job intake and review, served by the remote server. A job is created first, as a\n DRAFT; its file is then uploaded and attached to it, and the job is submitted.",
      "name": "server.v1.PrintJobService"
    },
    {
      "description": "The queues print jobs wait in, served by the remote server.",
      "name": "server.v1.PrinterQueueService"
    },
    {
      "description": "The printers the remote server knows of, with their latest reported state.",
      "name": "server.v1.PrinterService"
    }
  ]
};
