# LatMatrix: Work Distribution Plan (V1.2)

## Project Title: Summarizing Legal Documents in Easy Language  
### Sponsor: Industry Client | Mentor: Course Coordinator  

### 1. Project Management & Governance  
- **Role:** Project Coordinator
- **Primary Focus:** Project Coordination & Documentation  
- **Secondary Focus:** UX/UI & User Workflow Enhancement  
- **Description:** Collecting and updating product requirements, maintaining project specifications and design documents, testing UI features, and ensuring the final output aligns with the requirements set by the client.

### 2. Lead Architecture & Integration  
- **Role:** Lead Architect
- **Primary Focus:** System Design & Quality Assurance, NLP and OCR Pipeline Integration  
- **Secondary Focus:** Developer Workflow Management, AI Pipeline Engineering, Assigning Development Tasks  
- **Description:** Defining the high-level architecture for the summarization, overseeing code merges, researching, designing, and optimizing the AI pipeline.

### 3. Backend & AI Services  
- **Role:** Backend & AI Engineer
- **Primary Focus:** Legal Summarization Logic & Text Extraction  
- **Description:** Responsible for implementing robust backend services for high-fidelity text extraction, natural language processing, and summarization. This role specifically manages the "Easy Language" translation logic and develops the automated testing suite to evaluate the integration between the extraction services and the user interface.  
- **AI & Extraction Goals:** Owns the server-side pipeline that transforms raw legal documents into structured data ready for the NLP model, ensuring the backend can scale with complex document layouts.

### 4. Frontend UI & AI Integration  
- **Role:** Frontend & AI Integration Engineer
- **Primary Focus:** Interface & Document Visualization  
- **Description:** Responsible for designing the document upload dashboard and the "split-view" interface (Original vs. Easy Language). This role collaborates directly on the text extraction workflow by building frontend validation tools that allow users to verify extracted segments before they are processed by the AI.  
- **AI & Extraction Goals:** Implements the user-facing side of the AI services, ensuring that real-time text rendering and summarization feedback are intuitive and that user corrections are fed back into the extraction logic for better accuracy.

### 5. Backend, DevOps & Cybersecurity  
- **Role:** Backend, DevOps & Security Engineer
- **Primary Focus:** Secure Deployment, Data Integrity & System Testing  
- **Description:** Responsible for architecting a hardened server environment for the storage of sensitive legal documents and managing automated deployment pipelines. This role bridges the gap between development and production by implementing comprehensive unit and integration testing suites to ensure the reliability of the API connections between the frontend and the AI summarization model.  
- **Cybersecurity & DevOps Goals:** Implements robust security protocols such as encryption and access controls to protect "Commercial-in-Confidence" information. Manages the CI/CD workflow, database schema migrations, and resource monitoring to ensure the AI text extraction services remain performant and secure under load.

## Next Steps for the Team  
- **Task Population:** Each member should fill in their top 3 priorities for the current sprint.  
- **Sponsor Review:** Share the updated distribution with the client to ensure role alignment.  