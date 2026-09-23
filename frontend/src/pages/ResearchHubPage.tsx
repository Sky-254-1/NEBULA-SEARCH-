import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '@/api/client';
import { useAuth } from '@/context/AuthContext';
import { withRetry } from '@/utils/errorHandling';
import './ResearchHubPage.css';

interface Project {
  id: string;
  title: string;
  description?: string;
  tags: string[];
  is_archived: boolean;
  created_at: string;
  updated_at: string;
  note_count: number;
  bookmark_count: number;
}

interface Note {
  id: string;
  project_id: string;
  title: string;
  content: string;
  source_url?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

interface Bookmark {
  id: string;
  project_id: string;
  url: string;
  title: string;
  description?: string;
  tags: string[];
  created_at: string;
}

export function ResearchHubPage() {
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [showCreateProject, setShowCreateProject] = useState(false);
  const [showCreateNote, setShowCreateNote] = useState(false);
  const [showCreateBookmark, setShowCreateBookmark] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const queryClient = useQueryClient();
  const { user } = useAuth();

  // Fetch projects
  const { data: projects, isLoading: projectsLoading } = useQuery({
    queryKey: ['research-projects'],
    queryFn: async () => {
      return withRetry(async () => {
        const response = await apiClient.get<Project[]>('/research/projects');
        return response;
      });
    },
  });

  // Fetch notes for selected project
  const { data: notes, isLoading: notesLoading } = useQuery({
    queryKey: ['research-notes', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      return withRetry(async () => {
        const response = await apiClient.get<Note[]>(
          `/research/projects/${selectedProject.id}/notes`
        );
        return response;
      });
    },
    enabled: !!selectedProject,
  });

  // Fetch bookmarks for selected project
  const { data: bookmarks, isLoading: bookmarksLoading } = useQuery({
    queryKey: ['research-bookmarks', selectedProject?.id],
    queryFn: async () => {
      if (!selectedProject) return [];
      return withRetry(async () => {
        const response = await apiClient.get<Bookmark[]>(
          `/research/projects/${selectedProject.id}/bookmarks`
        );
        return response;
      });
    },
    enabled: !!selectedProject,
  });

  // Create project mutation
  const createProjectMutation = useMutation({
    mutationFn: async (data: { title: string; description?: string; tags: string[] }) => {
      return withRetry(async () => {
        const response = await apiClient.post<Project>('/research/projects', data);
        return response;
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['research-projects'] });
      setShowCreateProject(false);
    },
  });

  // Create note mutation
  const createNoteMutation = useMutation({
    mutationFn: async (data: { project_id: string; title: string; content: string; source_url?: string; tags: string[] }) => {
      return withRetry(async () => {
        const response = await apiClient.post<Note>('/research/notes', data);
        return response;
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['research-notes'] });
      setShowCreateNote(false);
    },
  });

  // Create bookmark mutation
  const createBookmarkMutation = useMutation({
    mutationFn: async (data: { project_id: string; url: string; title: string; description?: string; tags: string[] }) => {
      return withRetry(async () => {
        const response = await apiClient.post<Bookmark>('/research/bookmarks', data);
        return response;
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['research-bookmarks'] });
      setShowCreateBookmark(false);
    },
  });

  // Delete project mutation
  const deleteProjectMutation = useMutation({
    mutationFn: async (projectId: string) => {
      return withRetry(async () => {
        await apiClient.delete(`/research/projects/${projectId}`);
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['research-projects'] });
      setSelectedProject(null);
    },
  });

  // Filter projects based on search
  const filteredProjects = projects?.filter(project => 
    project.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.description?.toLowerCase().includes(searchQuery.toLowerCase()) ||
    project.tags.some(tag => tag.toLowerCase().includes(searchQuery.toLowerCase()))
  ) || [];

  return (
    <div className="research-hub">
      <header className="research-header">
        <h1>Research Hub</h1>
        <p className="research-subtitle">Collaborative research and knowledge management</p>
      </header>

      <div className="research-container">
        {/* Sidebar - Projects List */}
        <aside className="research-sidebar">
          <div className="sidebar-header">
            <input
              type="text"
              placeholder="Search projects..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
            <button
              onClick={() => setShowCreateProject(true)}
              className="btn-primary"
            >
              + New Project
            </button>
          </div>

          <div className="projects-list">
            {projectsLoading ? (
              <div className="loading">Loading projects...</div>
            ) : filteredProjects.length === 0 ? (
              <div className="empty-state">
                <p>No projects found</p>
                <button
                  onClick={() => setShowCreateProject(true)}
                  className="btn-secondary"
                >
                  Create your first project
                </button>
              </div>
            ) : (
              filteredProjects.map(project => (
                <div
                  key={project.id}
                  className={`project-card ${selectedProject?.id === project.id ? 'selected' : ''}`}
                  onClick={() => setSelectedProject(project)}
                >
                  <h3>{project.title}</h3>
                  {project.description && (
                    <p className="project-description">{project.description}</p>
                  )}
                  <div className="project-meta">
                    {project.tags.slice(0, 3).map(tag => (
                      <span key={tag} className="tag">{tag}</span>
                    ))}
                  </div>
                  <div className="project-stats">
                    <span>📝 {project.note_count} notes</span>
                    <span>🔖 {project.bookmark_count} bookmarks</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </aside>

        {/* Main Content */}
        <main className="research-content">
          {selectedProject ? (
            <>
              <div className="project-header">
                <div>
                  <h2>{selectedProject.title}</h2>
                  {selectedProject.description && (
                    <p>{selectedProject.description}</p>
                  )}
                  <div className="project-tags">
                    {selectedProject.tags.map(tag => (
                      <span key={tag} className="tag">{tag}</span>
                    ))}
                  </div>
                </div>
                <div className="project-actions">
                  <button
                    onClick={() => setShowCreateNote(true)}
                    className="btn-primary"
                  >
                    + Add Note
                  </button>
                  <button
                    onClick={() => setShowCreateBookmark(true)}
                    className="btn-secondary"
                  >
                    + Add Bookmark
                  </button>
                  <button
                    onClick={() => deleteProjectMutation.mutate(selectedProject.id)}
                    className="btn-danger"
                  >
                    Delete
                  </button>
                </div>
              </div>

              {/* Tabs */}
              <div className="research-tabs">
                <button className="tab active">Notes</button>
                <button className="tab">Bookmarks</button>
                <button className="tab">Citations</button>
              </div>

              {/* Notes List */}
              <div className="notes-list">
                {notesLoading ? (
                  <div className="loading">Loading notes...</div>
                ) : notes?.length === 0 ? (
                  <div className="empty-state">
                    <p>No notes yet</p>
                    <button
                      onClick={() => setShowCreateNote(true)}
                      className="btn-primary"
                    >
                      Create your first note
                    </button>
                  </div>
                ) : (
                  notes?.map(note => (
                    <div key={note.id} className="note-card">
                      <h4>{note.title}</h4>
                      <p>{note.content}</p>
                      {note.source_url && (
                        <a href={note.source_url} target="_blank" rel="noopener noreferrer">
                          Source
                        </a>
                      )}
                      <div className="note-tags">
                        {note.tags.map(tag => (
                          <span key={tag} className="tag">{tag}</span>
                        ))}
                      </div>
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="no-project-selected">
              <h2>Select a project or create a new one</h2>
              <p>Organize your research with projects, notes, and bookmarks</p>
            </div>
          )}
        </main>
      </div>

      {/* Create Project Modal */}
      {showCreateProject && (
        <div className="modal-overlay" onClick={() => setShowCreateProject(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Create New Project</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                createProjectMutation.mutate({
                  title: formData.get('title') as string,
                  description: formData.get('description') as string,
                  tags: (formData.get('tags') as string).split(',').map(t => t.trim()).filter(Boolean),
                });
              }}
            >
              <input
                name="title"
                placeholder="Project title"
                required
                className="input"
              />
              <textarea
                name="description"
                placeholder="Description (optional)"
                className="textarea"
              />
              <input
                name="tags"
                placeholder="Tags (comma-separated)"
                className="input"
              />
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateProject(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={createProjectMutation.isPending}>
                  Create
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Note Modal */}
      {showCreateNote && selectedProject && (
        <div className="modal-overlay" onClick={() => setShowCreateNote(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Add Note</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                createNoteMutation.mutate({
                  project_id: selectedProject.id,
                  title: formData.get('title') as string,
                  content: formData.get('content') as string,
                  source_url: formData.get('source_url') as string || undefined,
                  tags: (formData.get('tags') as string).split(',').map(t => t.trim()).filter(Boolean),
                });
              }}
            >
              <input
                name="title"
                placeholder="Note title"
                required
                className="input"
              />
              <textarea
                name="content"
                placeholder="Note content"
                required
                className="textarea"
                rows={6}
              />
              <input
                name="source_url"
                placeholder="Source URL (optional)"
                className="input"
              />
              <input
                name="tags"
                placeholder="Tags (comma-separated)"
                className="input"
              />
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateNote(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={createNoteMutation.isPending}>
                  Add Note
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Create Bookmark Modal */}
      {showCreateBookmark && selectedProject && (
        <div className="modal-overlay" onClick={() => setShowCreateBookmark(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>Add Bookmark</h2>
            <form
              onSubmit={(e) => {
                e.preventDefault();
                const formData = new FormData(e.target);
                createBookmarkMutation.mutate({
                  project_id: selectedProject.id,
                  url: formData.get('url') as string,
                  title: formData.get('title') as string,
                  description: formData.get('description') as string || undefined,
                  tags: (formData.get('tags') as string).split(',').map(t => t.trim()).filter(Boolean),
                });
              }}
            >
              <input
                name="url"
                type="url"
                placeholder="URL"
                required
                className="input"
              />
              <input
                name="title"
                placeholder="Title"
                required
                className="input"
              />
              <input
                name="description"
                placeholder="Description (optional)"
                className="input"
              />
              <input
                name="tags"
                placeholder="Tags (comma-separated)"
                className="input"
              />
              <div className="modal-actions">
                <button type="button" onClick={() => setShowCreateBookmark(false)} className="btn-secondary">
                  Cancel
                </button>
                <button type="submit" className="btn-primary" disabled={createBookmarkMutation.isPending}>
                  Add Bookmark
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}