Data management choices
=======================

A conceptual data-flow design for the print farm management system, including service responsibilities, core entities, and endpoint groupings.

1\. Purpose
-----------

This document outlines how data will flow between the services that make up the new print farm management system. It identifies the services involved, the core data entities each owns, the major data flows between them, and a high-level grouping of the endpoints each flow will need.

2\. System overview
-------------------

Client App:
Single web application with role-gated views (Student, Staff, Admin, Guest). Students upload/slice/submit jobs and view their own job status.

Desktop App:
Desktop application used by staff to manage printer fleets, view reports and send notifications.

Backend API:
Core business logic: auth, users, queues, fleet/printers/tags /sections, print jobs, filament tracking, notifications, reporting.

Primary Database:
Relational store backing the backend (users, jobs, queues, printers, tags, sections, filament ledger, etc.).

File Storage:
Separate store for GCODE and model files, kept apart from the relational DB since these are large binary objects, not rows.

Prusa Connect Local (PCL):
Runs on university infrastructure. Dispatches jobs to printers and reports printer status back.

**Notes on decisions already made:**

*   The system will not integrate with the existing Makerspace database. Users create separate credentials, stored in this system's own database, holding only what's needed for user-print-management.
*   Fleet partitioning uses Fleet Sections, and each printer belongs to exactly one section (e.g. self-service, general use).

3\. Core data entities
----------------------

These are described at a conceptual level.

*   **User:** account with a role (Student, Staff, Moderator, Admin, Guest) and, for students, a filament allocation balance.
*   **Printer:** a physical printer: id, model/type, capabilities, current status, and the Fleet Section it belongs to.
*   **Tag:** a flexible label on printers (e.g. self-serve, mk4s, room-204) used for search/filtering (dependent on PCL).
*   **Fleet Section:** a named partition of the fleet. Staff/admin users subscribe to a section to see and manage only the printers within it.
*   **Queue:** a logical line for print jobs, organized around courses, clubs, or events. Targets a type of job, not a specific printer.
*   **PrintJob:** a submitted print including student, file reference, queue, current status, assigned printer (structure dependent on PCL).
*   **Filament Ledger:** tracks each student's allocation and usage over time.
*   **Notification:** a triggered message (per-job status update, or a staff-initiated mass email to a group/queue).

4\. Data flows
--------------

### 4.1 Account creation and auth

Web App → Backend → Database. Backend issues and validates credentials against its own user store.

### 4.2 Print submission

*   Student uploads a GCODE (or sliceable model) file through the Web App.
*   File is stored in File Storage; the Backend stores a reference to it (not the file itself) on a new PrintJob record.
*   Staff places the PrintJob into the appropriate Queue.

**Endpoint cluster:** GCODE/model upload (create/list/ delete uploaded files), job submission.

### 4.3 Job dispatch and file transfer to printer

First step: staff pull a job from a backend Queue represented in the Desktop App and assign it to a printer within a Fleet Section they're operating. This triggers a dispatch request from Desktop App → Backend.

#### PCL fetches directly from File Storage

The Backend only passes PCL a reference to the file (an ID or pre-signed URL) via a lightweight REST call. PCL fetches the file bytes from File Storage.

**Endpoint cluster:** Job dispatch (assign to printer, cancel, restart).

### 4.4 Printer status reporting

PCL reports status via periodic webhook calls to a backend endpoint, or the backend polls a PCL status endpoint on an interval. Less real-time and more request/response overhead than a persistent stream.

### 4.5 Real-time status delivery to users

*   **Staff/Admin (section views):** Server-Sent Events (SSE) from backend to user. The backend sends updates to the Fleet Section the user is subscribed to, so a user only receives updates for printers they're actually watching.
*   **Students:** a polling endpoint returning the status of all jobs belonging to the requesting student, backed by the backend's cached current-state (not a direct DB hit per poll) to keep this cheap at scale. Students don't need too many push notifications; prints run over hours, and they aren't continuously watching.

### 4.6 Filament allocation and usage tracking

Backend deducts from a student's filament balance as jobs are dispatched/completed and logs usage to the Filament Ledger for reporting. Triggers an automatic low-balance notification.

### 4.7 Notifications

Backend triggers a single, consolidated status notification per meaningful job event (addressing the email-spam issue in the current system). This includes staff-initiated mass emails to a queue, course, or group.

### 4.8 Reporting

Backend aggregates filament usage, print time, and user counts from the Database to produce admin-facing reports, replacing the PrinterOS statistics page.

5\. Fleet partitioning recap
----------------------------

Printers are organized into Fleet Sections, with each printer belonging to exactly one section. Tags remain available for flexible search/filtering within and across sections, but sections are the primary unit for both access partitioning and SSE subscription scope. This is what lets a client (e.g. the self-serve kiosk) only receive updates for the printers it cares about, addressing the performance problems of the current system rendering and holding state for the entire fleet regardless of view.

6\. Endpoint cluster summary
----------------------------

All core-domain logic should follow Domain-Driven Design (DDD) architecture and these are our suggested first domains. It may be subject to change

High-level groupings:

*   **Auth / Account:** credential creation, login, session management
*   **GCODE/Model Upload:** CRUD for uploaded files
*   **Queue Management:** create/list queues, manage student access
*   **Job Submission & Dispatch:** submit job, assign to printer, cancel, restart
*   **Fleet / Printer Management:** CRUD for printers, tags, Fleet Sections
*   **Filament Allocation:** balance queries, allocation adjustments, usage logs
*   **Notifications:** per-job notification triggers, mass email
*   **Reporting:** usage, print time, and user-count aggregation
*   **Real-Time Status:** SSE subscription endpoint (staff), polling endpoint (students)