# Data Flow (Screen ↔ Data Source)

```mermaid
%%{init:{'theme':'base','themeVariables':{'background':'#060810','primaryColor':'#0c1a30','primaryTextColor':'#7dd3fc','primaryBorderColor':'#0e3a6e','edgeLabelBackground':'#0c1a30','lineColor':'#334155','secondaryColor':'#0f172a','clusterBkg':'#060c18','clusterBorder':'#1e3a5f','fontFamily':'JetBrains Mono','fontSize':'14'}}}%%
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
  classDef apiAxios fill:#1a0d1a,stroke:#a855f7,color:#e9d5ff
  classDef apiFetch fill:#0d1a1a,stroke:#06b6d4,color:#a5f3fc
  classDef apiQuery fill:#1a0d0d,stroke:#f43f5e,color:#fecdd3
  route_frontend_src_App_jsx__["/ · CSR"]:::csr
  ep_GET_q["GET q → axios"]:::apiAxios
  ep_GET_auth["GET auth → axios"]:::apiAxios
  route_Nebula_search_engine__main_frontend_src_App_jsx__["/ · CSR"]:::csr
  route__kilo_worktrees_daffy_grain_frontend_src_App_jsx__["/ · CSR"]:::csr
  route__kilo_worktrees_exciting_quokka_frontend_src_App_jsx__["/ · CSR"]:::csr
  route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__["/ · CSR"]:::csr
  route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__["/ · CSR"]:::csr
  subgraph HISTORY_API["📄 /history"]
    route_frontend_src_App_jsx__history["history · CSR"]:::csr
    route_Nebula_search_engine__main_frontend_src_App_jsx__history["history · CSR"]:::csr
    route__kilo_worktrees_daffy_grain_frontend_src_App_jsx__history["history · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_frontend_src_App_jsx__history["history · CSR"]:::csr
    route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__history["history · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__history["history · CSR"]:::csr
  end
  subgraph LEGACY_API["📄 /legacy"]
    route_frontend_src_App_jsx__legacy["legacy · CSR"]:::csr
    route_Nebula_search_engine__main_frontend_src_App_jsx__legacy["legacy · CSR"]:::csr
    route__kilo_worktrees_daffy_grain_frontend_src_App_jsx__legacy["legacy · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_frontend_src_App_jsx__legacy["legacy · CSR"]:::csr
    route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__legacy["legacy · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__legacy["legacy · CSR"]:::csr
  end
  subgraph OAUTH_API["📄 /oauth"]
    route_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback["callback · CSR"]:::csr
    ep_GET_error["GET error → axios"]:::apiAxios
    ep_GET_access_token["GET access_token → axios"]:::apiAxios
    ep_GET_refresh_token["GET refresh_token → axios"]:::apiAxios
    route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback["callback · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback["callback · CSR"]:::csr
  end
  subgraph SEARCH_API["📄 /search"]
    route_Nebula_search_engine__main_frontend_src_App_jsx__search["search · CSR"]:::csr
    route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__search["search · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__search["search · CSR"]:::csr
  end
  subgraph DASHBOARD_API["📄 /dashboard"]
    route_Nebula_search_engine__main_frontend_src_App_jsx__dashboard["dashboard · CSR"]:::csr
    route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__dashboard["dashboard · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__dashboard["dashboard · CSR"]:::csr
  end
  subgraph PROFILE_API["📄 /profile"]
    route_Nebula_search_engine__main_frontend_src_App_jsx__profile["profile · CSR"]:::csr
    route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__profile["profile · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__profile["profile · CSR"]:::csr
  end
  subgraph SETTINGS_API["📄 /settings"]
    route_Nebula_search_engine__main_frontend_src_App_jsx__settings["settings · CSR"]:::csr
    route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__settings["settings · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__settings["settings · CSR"]:::csr
  end
  subgraph ANALYTICS_API["📄 /analytics"]
    route_Nebula_search_engine__main_frontend_src_App_jsx__analytics["analytics · CSR"]:::csr
    route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__analytics["analytics · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__analytics["analytics · CSR"]:::csr
  end
  subgraph ADMIN_API["⚙ /admin"]
    route_Nebula_search_engine__main_frontend_src_App_jsx__admin["admin · CSR"]:::csr
    route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__admin["admin · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__admin["admin · CSR"]:::csr
  end
  subgraph DOCUMENTS_API["📄 /documents"]
    route_Nebula_search_engine__main_frontend_src_App_jsx__documents["documents · CSR"]:::csr
    route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__documents["documents · CSR"]:::csr
    route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__documents["documents · CSR"]:::csr
  end
  route_frontend_src_App_jsx__ --> ep_GET_q
  route_frontend_src_App_jsx__ --> ep_GET_auth
  route_Nebula_search_engine__main_frontend_src_App_jsx__ --> ep_GET_q
  route_Nebula_search_engine__main_frontend_src_App_jsx__ --> ep_GET_auth
  route__kilo_worktrees_daffy_grain_frontend_src_App_jsx__ --> ep_GET_q
  route__kilo_worktrees_daffy_grain_frontend_src_App_jsx__ --> ep_GET_auth
  route__kilo_worktrees_exciting_quokka_frontend_src_App_jsx__ --> ep_GET_q
  route__kilo_worktrees_exciting_quokka_frontend_src_App_jsx__ --> ep_GET_auth
  route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__ --> ep_GET_q
  route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__ --> ep_GET_auth
  route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__ --> ep_GET_q
  route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__ --> ep_GET_auth
  route_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback --> ep_GET_error
  route_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback --> ep_GET_access_token
  route_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback --> ep_GET_refresh_token
  route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback --> ep_GET_error
  route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback --> ep_GET_access_token
  route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback --> ep_GET_refresh_token
  route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback --> ep_GET_error
  route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback --> ep_GET_access_token
  route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__oauth_callback --> ep_GET_refresh_token
  route_Nebula_search_engine__main_frontend_src_App_jsx__search --> ep_GET_q
  route__kilo_worktrees_daffy_grain_Nebula_search_engine__main_frontend_src_App_jsx__search --> ep_GET_q
  route__kilo_worktrees_exciting_quokka_Nebula_search_engine__main_frontend_src_App_jsx__search --> ep_GET_q
```
