# The UUID the database stores for each enum member. A stored row means whatever its UUID meant
# when it was written, so a UUID is never changed or given to another member, even after the
# member is removed. Numbers and names are never stored: proto numbering or a rename would change
# the meaning of existing rows.
from uuid import UUID

from core_domain.file import FileType
from core_domain.print_job import PrintJobStatus
from proto_utils.gen.user.v1 import user_pb2

PRINT_JOB_STATUS_IDS: dict[PrintJobStatus, UUID] = {
    PrintJobStatus.DRAFT: UUID("2c5216d8-6fe3-4a53-b079-a09029538dc7"),
    PrintJobStatus.SUBMITTED: UUID("e187258b-c571-4e02-a41b-40ff99055e7e"),
    PrintJobStatus.UNDER_REVIEW: UUID("1a56f1ad-9dbf-4f8c-8b03-d0324b90c1e7"),
    PrintJobStatus.APPROVED: UUID("f2270cdc-6045-4b6e-8355-79bc5c74fa4b"),
    PrintJobStatus.REJECTED: UUID("a7d7356f-0c22-4bb2-b337-6a3414b07b69"),
    PrintJobStatus.ASSIGNED: UUID("99aed946-c095-4722-b17c-2d341b65a957"),
    PrintJobStatus.PRINTING: UUID("8aecac58-9b53-4f97-a85a-f881a14271b1"),
    PrintJobStatus.FINISHED: UUID("aa46d3f2-c2d4-4bfd-ab8c-56cd91c68602"),
    PrintJobStatus.COMPLETED: UUID("592d3ded-36eb-4aac-9f00-5c3caa60c5c7"),
    PrintJobStatus.FAILED: UUID("2d4b7a77-f073-40d2-bdb3-d33cdbf7e111"),
    PrintJobStatus.CANCELLED: UUID("9657b139-8f59-496d-b7da-1289309c5dae"),
}

FILE_TYPE_IDS: dict[FileType, UUID] = {
    FileType.GCODE: UUID("4565c182-f698-4e1a-a2a9-b33e92254dbe"),
    FileType.CGCODE: UUID("cb19af65-7390-4f2a-9282-b1dc656f3cf3"),
}

USER_ROLE_IDS: dict[user_pb2.UserRole, UUID] = {
    user_pb2.USER_ROLE_GUEST: UUID("17051c1b-afa2-46f9-a9cf-12f9b250b8bb"),
    user_pb2.USER_ROLE_STUDENT: UUID("e398f1da-6203-4d85-894e-838de08c35e5"),
    user_pb2.USER_ROLE_STAFF: UUID("44136de6-0927-47ea-8763-4e93ae2a27f8"),
    user_pb2.USER_ROLE_ADMIN: UUID("47cd9afe-e69d-4e20-9839-e19cf2c71f84"),
}

# Members the dev seed needs whose enums are not in packages/proto yet. Each moves into a map
# above, keeping its UUID, when the feature that uses it adds the proto enum.
USER_STATUS_ACTIVE_ID = UUID("fcbfe76e-3ec2-468e-b0b4-4c61a3045622")
FLEET_ACCESS_POLICY_STAFF_ONLY_ID = UUID("0893e1a6-e0b8-4035-b001-d08f352398a4")
FILE_UPLOAD_STATUS_UPLOADED_ID = UUID("5595dd8f-0bf9-4943-8e45-47a796dda538")
FILE_SCAN_STATUS_CLEAN_ID = UUID("cf2ae902-1b0d-4a06-a1d8-56d7552203d7")
