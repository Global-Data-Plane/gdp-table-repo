# GDP Repo API Test Matrix

## Table

| Endpoint          | Method | Auth?  | Params / Body    | Success | Error cases                                      |
|-------------------|--------|--------|------------------|---------|--------------------------------------------------|
| /tables           | GET    | Yes    | -                | 200     | Unauthenticated (should be 400)                  |
| /upload/<name>    | POST   | Yes    | SDML (JSON/file) | 200     | Missing table, bad content-type, unauth, bad ext |
| /table/<key>      | GET    | Yes    | -                | 200     | Not permitted (403), not found (404)             |
| /delete/<name>    | DELETE | Yes    | -                | 200     | Not found (404), unauth                          |
| /share/<name>     | POST   | Yes    | JSON {share:[]}  | 200     | Not found (404), bad body, unauth                |

## Example Test Cases

### 1. Upload Table

- **POST /upload/mytable**
    - As owner, JSON: `{ "table": "<valid SDML>" }` → 200, returns key
    - Missing table in JSON → 400
    - As owner, multipart/form with `table` file → 200
    - Missing file in form → 400
    - Unsupported content-type → 400
    - No auth → 400

### 2. List Tables

- **GET /tables**
    - As owner → 200, gets own tables
    - As shared user → 200, gets shared tables
    - As unauthenticated → 400

### 3. Download Table

- **GET /table/<owner>/mytable.sdml**
    - Owner → 200, gets table
    - Shared user → 200, gets table
    - Unauthorized user → 403
    - Not found → 404

### 4. Delete Table

- **DELETE /delete/mytable.sdml**
    - Owner → 200, table deleted
    - Non-owner → 400 or 404
    - Table not found → 404

### 5. Share Table

- **POST /share/mytable.sdml** with JSON `{"share": ["user2@ai"]}`
    - Owner → 200, share updated
    - Bad JSON body (missing or wrong type) → 400
    - Table not found → 404
    - Unauth → 400

---

## Edge Cases

- Table name with/without `.sdml` extension on upload
- Attempting actions with missing or malformed headers
- Share list is not a list (string, number, etc.)
- Deleting/Sharing a table not owned by the user

---

*Generated for Rick & Aiko — 2025-09-21*
