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
      "id.v1.QueueId": {
        "additionalProperties": false,
        "description": "Identifies a queue.",
        "properties": {
          "value": {
            "description": "UUID.",
            "title": "value",
            "type": "string"
          }
        },
        "title": "QueueId",
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
          "queueId": {
            "allOf": [
              {
                "$ref": "#/components/schemas/id.v1.QueueId"
              }
            ],
            "description": "The queue staff placed it in after approval. Students never choose it.",
            "title": "queue_id"
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
          "PRINT_JOB_STATUS_COMPLETED",
          "PRINT_JOB_STATUS_FAILED",
          "PRINT_JOB_STATUS_CANCELLED"
        ],
        "title": "PrintJobStatus",
        "type": "string"
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
        "description": "Chooses the printer for an APPROVED job, moving it to ASSIGNED.",
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
    "/server.v1.PrintJobService/CreatePrintJob": {
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
    "/server.v1.PrintJobService/CreatePrintJobUpload": {
      "post": {
        "description": "Step 2, and upload pair call 1 of 2. Creates the job's file record, links it to the job,\r\n and returns where to PUT the bytes (call 2 of 2). Calling it again replaces the file.",
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
    "/server.v1.PrintJobService/GetPrintJob": {
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
    "/server.v1.PrintJobService/ListPrintJobs": {
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
    "/server.v1.PrintJobService/SubmitPrintJob": {
      "post": {
        "description": "Step 3. Submits a DRAFT job whose file has finished uploading, moving it to SUBMITTED.",
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
    "/server.v1.PrintJobService/TransitionPrintJob": {
      "post": {
        "description": "Staff move a job to its next status. Each action carries exactly the fields it needs; the\r\n server rejects an action that is not valid from the job's current status.",
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
    }
  },
  "tags": [
    {
      "description": "Reports server health, for monitoring and deployment checks.",
      "name": "server.v1.HealthCheckService"
    },
    {
      "description": "Print job intake and review, served by the remote server. A job is created first, as a\r\n DRAFT; its file is then uploaded and attached to it, and the job is submitted.",
      "name": "server.v1.PrintJobService"
    }
  ]
};
