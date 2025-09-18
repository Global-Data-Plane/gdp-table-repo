# GDP Table Repo

*A secure, reference repository and service for SDML tables in the Global Data Plane (GDP) ecosystem.*

---

## What is GDP Table Repo?

**GDP Table Repo** is the canonical repository and server for SDML (Simple Data Markup Language) tables, powering the Global Data Plane (GDP) and its community of data-driven applications.

- **Authoritative**: Stores and serves SDML tables as the source of truth.
- **Secure**: Access is managed via OAuth or other provider-based authentication.
- **Reference Implementation**: Includes a minimal, public server for SDML tables — ready to run, extend, or integrate.

---

## Features

- **Central SDML Table Store:** All reference tables, schemas, and updates live here.
- **Access Control:** Only authorized users may publish, update, or manage tables (via OAuth or compatible provider).
- **API-first:** RESTful endpoints for listing, retrieving, and (for authorized users) publishing tables.
- **Open Documentation:** API specs, SDML/SDTP guides, and usage examples included.

---

## What's in this Repository?

- **`server/`**  
  Minimal SDML Table Service implementation (Python/FastAPI, Go, or your tech of choice).

- **`tables/`**  
  Reference SDML table files and example data.

- **`docs/`**  
  Guides, API docs, usage recipes, and best practices.

- **`README.md`**  
  This file — overview, goals, and getting started info.

---

## How to Use or Contribute

1. **Clone the repo**  
   `git clone https://github.com/global-data-plane/gdp-table-repo.git`

2. **Run the Table Service**  
   See `server/README.md` for setup and quick start.

3. **API Usage**  
   Explore the REST API for table retrieval and management (see `docs/API.md`).

4. **Access Control**  
   Authentication required for publishing or updating tables. (OAuth config details in `server/README.md`.)

5. **Contribute**  
   PRs for code, docs, or example tables welcome! Access for publishing managed by GDP admins.

---

## License

MIT License (see [LICENSE](LICENSE) for details)

---

## About the Global Data Plane

The Global Data Plane (GDP) is an open architecture for secure, interoperable, and federated data exchange.  
Learn more at ([https://globaldataplane.org](https://global-data-plane.github.io/).

---

*Maintained by the Global Data Plane community. Access is managed; see the README for details.*

