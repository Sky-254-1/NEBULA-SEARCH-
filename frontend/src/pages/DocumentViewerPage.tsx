import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Download, Share2, ZoomIn, ZoomOut, Maximize, FileText, Loader2 } from 'lucide-react';
import { toast } from 'react-hot-toast';

export const DocumentViewerPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [isLoading, setIsLoading] = useState(true);
  const [document, setDocument] = useState<any>(null);
  const [zoom, setZoom] = useState(100);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);

  useEffect(() => {
    if (id) {
      loadDocument(parseInt(id));
    }
  }, [id]);

  const loadDocument = async (documentId: number) => {
    try {
      const response = await fetch(`/api/v1/documents/${documentId}`);
      if (response.ok) {
        const data = await response.json();
        setDocument(data);
        setTotalPages(data.pages || 1);
      } else {
        toast.error('Failed to load document');
      }
    } catch (error) {
      toast.error('Failed to load document');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDownload = async () => {
    if (!document) return;
    try {
      const response = await fetch(`/api/v1/documents/${id}/download`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = document.filename;
        a.click();
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      toast.error('Failed to download document');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <Loader2 className="animate-spin text-blue-600 mx-auto" size={40} />
          <p className="text-gray-600 dark:text-gray-300">Loading document...</p>
        </div>
      </div>
    );
  }

  if (!document) {
    return (
      <div className="max-w-4xl mx-auto text-center py-12">
        <FileText className="mx-auto text-gray-400 mb-4" size={64} />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          Document Not Found
        </h2>
        <p className="text-gray-600 dark:text-gray-300 mb-6">
          The document you're looking for doesn't exist or has been deleted.
        </p>
        <button
          onClick={() => navigate('/documents')}
          className="inline-flex items-center gap-2 text-blue-600 hover:text-blue-700"
        >
          <ArrowLeft size={20} />
          Back to Documents
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-4">
      {/* Top Bar */}
      <div className="flex items-center justify-between bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate('/documents')}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg transition-colors"
          >
            <ArrowLeft size={20} />
          </button>
          <div>
            <h1 className="text-lg font-semibold text-gray-900 dark:text-white">
              {document.filename}
            </h1>
            <p className="text-sm text-gray-500 dark:text-gray-400">
              {document.content_type || 'Unknown type'} • {document.file_size || 'Unknown size'}
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={handleDownload}
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg transition-colors"
            title="Download"
          >
            <Download size={20} />
          </button>
          <button
            className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 rounded-lg transition-colors"
            title="Share"
          >
            <Share2 size={20} />
          </button>
        </div>
      </div>

      {/* Document Viewer */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {/* Toolbar */}
        <div className="flex items-center justify-between px-4 py-2 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
          <div className="flex items-center gap-2">
            <button
              onClick={() => setZoom(Math.max(25, zoom - 25))}
              className="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 rounded transition-colors"
            >
              <ZoomOut size={18} />
            </button>
            <span className="text-sm text-gray-600 dark:text-gray-400 w-16 text-center">
              {zoom}%
            </span>
            <button
              onClick={() => setZoom(Math.min(200, zoom + 25))}
              className="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 rounded transition-colors"
            >
              <ZoomIn size={18} />
            </button>
            <button
              onClick={() => setZoom(100)}
              className="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 px-2 py-1 rounded transition-colors"
            >
              Fit
            </button>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage(Math.max(1, page - 1))}
              disabled={page <= 1}
              className="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 rounded disabled:opacity-50 transition-colors"
            >
              Prev
            </button>
            <span className="text-sm text-gray-600 dark:text-gray-400">
              Page {page} of {totalPages}
            </span>
            <button
              onClick={() => setPage(Math.min(totalPages, page + 1))}
              disabled={page >= totalPages}
              className="px-3 py-1 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-200 dark:hover:bg-gray-700 rounded disabled:opacity-50 transition-colors"
            >
              Next
            </button>
            <button className="p-1.5 text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 rounded transition-colors">
              <Maximize size={18} />
            </button>
          </div>
        </div>

        {/* Content Area */}
        <div
          className="flex items-start justify-center p-8 min-h-[500px] bg-gray-100 dark:bg-gray-900"
          style={{ transform: `scale(${zoom / 100})`, transformOrigin: 'top center' }}
        >
          <div className="bg-white dark:bg-gray-800 shadow-sm rounded-lg p-8 max-w-4xl w-full min-h-[600px]">
            {document.content_type?.startsWith('image/') ? (
              <img
                src={`/api/v1/documents/${id}/preview`}
                alt={document.filename}
                className="max-w-full h-auto mx-auto"
              />
            ) : document.content_type === 'application/pdf' ? (
              <iframe
                src={`/api/v1/documents/${id}/preview#page=${page}`}
                className="w-full h-[600px] border-0"
                title={document.filename}
              />
            ) : (
              <pre className="whitespace-pre-wrap font-sans text-gray-800 dark:text-gray-200 text-sm leading-relaxed">
                {document.content || 'No preview available'}
              </pre>
            )}
          </div>
        </div>
      </div>

      {/* Metadata Panel */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-4">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">
          Document Details
        </h3>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-gray-500 dark:text-gray-400">Name:</span>
            <span className="ml-2 text-gray-900 dark:text-white">{document.filename}</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Type:</span>
            <span className="ml-2 text-gray-900 dark:text-white">{document.content_type || 'Unknown'}</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Size:</span>
            <span className="ml-2 text-gray-900 dark:text-white">{document.file_size || 'Unknown'}</span>
          </div>
          <div>
            <span className="text-gray-500 dark:text-gray-400">Created:</span>
            <span className="ml-2 text-gray-900 dark:text-white">
              {document.created_at ? new Date(document.created_at).toLocaleDateString() : 'Unknown'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};