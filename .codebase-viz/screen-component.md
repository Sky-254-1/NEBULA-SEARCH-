# Screen–Component Mapping

```mermaid
%%{init:{'theme':'base','themeVariables':{'background':'#060810','primaryColor':'#0c1a30','primaryTextColor':'#7dd3fc','primaryBorderColor':'#0e3a6e','edgeLabelBackground':'#0c1a30','lineColor':'#334155','secondaryColor':'#0f172a','clusterBkg':'#060c18','clusterBorder':'#1e3a5f','fontFamily':'JetBrains Mono','fontSize':'14'},'flowchart':{'nodeSpacing':40,'rankSpacing':24,'padding':8}}}%%
graph LR
  classDef ssr fill:#0d1a0d,stroke:#16a34a,color:#86efac
  classDef csr fill:#2d1200,stroke:#c2410c,color:#fb923c
  classDef ssg fill:#1a0d1a,stroke:#7c3aed,color:#c4b5fd
  classDef isr fill:#1a1a0d,stroke:#ca8a04,color:#fde047
  classDef ppr fill:#0d1a2d,stroke:#2563eb,color:#93c5fd
  classDef unk fill:#1a1a1a,stroke:#6b7280,color:#9ca3af
  classDef pkg fill:#0c1018,stroke:#475569,color:#cbd5e1
  classDef muted fill:#0a0d14,stroke:#374151,color:#64748b,stroke-dasharray: 3 3
  classDef hdr fill:#06080f,stroke:#1e3a5f,color:#7dd3fc
  route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__["/ · CSR<br/>🔗 /"]:::csr
  file_component_frontend_src_pages_HomePage_jsx_HomePage["📂 frontend/src/pages<br/>📄 HomePage.jsx"]:::pkg
  route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__ --> file_component_frontend_src_pages_HomePage_jsx_HomePage
  leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__history["history · CSR<br/>🔗 /history<br/>📂 frontend/src/pages<br/>📄 HistoryPage.jsx"]:::csr
  subgraph LEGACY_T["📄 /legacy"]
    route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__legacy["legacy · CSR<br/>🔗 /legacy"]:::csr
  end
  subgraph OAUTH_T["📄 /oauth"]
    leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback["callback · CSR<br/>🔗 /oauth/callback<br/>📂 Nebula-search-engine--main/frontend/src/pages<br/>📄 OAuthCallback.jsx"]:::csr
  end
  leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__search["search · CSR<br/>🔗 /search<br/>📂 Nebula-search-engine--main/frontend/src/pages<br/>📄 SearchPage.jsx"]:::csr
  leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__dashboard["dashboard · CSR<br/>🔗 /dashboard<br/>📂 Nebula-search-engine--main/frontend/src/pages<br/>📄 DashboardPage.jsx"]:::csr
  leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__profile["profile · CSR<br/>🔗 /profile<br/>📂 Nebula-search-engine--main/frontend/src/pages<br/>📄 ProfilePage.jsx"]:::csr
  leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__settings["settings · CSR<br/>🔗 /settings<br/>📂 Nebula-search-engine--main/frontend/src/pages<br/>📄 SettingsPage.jsx"]:::csr
  leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__analytics["analytics · CSR<br/>🔗 /analytics<br/>📂 Nebula-search-engine--main/frontend/src/pages<br/>📄 AnalyticsPage.jsx"]:::csr
  leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__admin["admin · CSR<br/>🔗 /admin<br/>📂 Nebula-search-engine--main/frontend/src/pages<br/>📄 AdminPage.jsx"]:::csr
  leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__documents["documents · CSR<br/>🔗 /documents<br/>📂 Nebula-search-engine--main/frontend/src/pages<br/>📄 DocumentsPage.jsx"]:::csr
  leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__history ~~~ LEGACY_T ~~~ OAUTH_T ~~~ leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__search ~~~ leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__dashboard ~~~ leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__profile ~~~ leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__settings ~~~ leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__analytics ~~~ leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__admin ~~~ leaf_route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__documents
```
