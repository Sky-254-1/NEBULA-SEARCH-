import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Upload, FileText, Trash2, Loader2, Search, Filter } from 'lucide-react';
import { useDocumentStore } from '@/state';
import { toast } from 'react-hot-toast';

export const DocumentsPage: React.FC = () => {
  const { documents, isLoading, uploadProgress, error, fetchDocuments, uploadDocument, deleteDocument, clearError } = useDocumentStore();
  const [isDragging, setIsDragging] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  useEffect(() => {
    if (error) {
      toast.error(error);
      clearError();
    }
  }, [error, clearError]);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    const files = Array.from(e.dataTransfer.files);
    if (files.length > 0) {
      await handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    try {
      await uploadDocument(file);
      toast.success('Document uploaded successfully');
    } catch (error) {
      toast.error('Failed to upload document');
    }
  };

  const handleFileInputChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      await handleFileUpload(file);
    }
  };

  const handleDelete = async (documentId: number) => {
    if (window.confirm('Are you sure you want to delete this document?')) {
      try {
        await deleteDocument(documentId);
        toast.success('Document deleted');
      } catch (error) {
        toast.error('Failed to delete document');
      }
    }
  };

  const filteredDocuments = documents.filter(doc =>
    doc.filename.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
          Documents
        </h1>
        <p className="text-gray-600 dark:text-gray-300">
          Upload and manage your documents
        </p>
      </div>

      {/* Upload Area */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
          isDragging
            ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
            : 'border-gray-300 dark:border-gray-600 hover:border-gray-400'
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <Upload className="mx-auto text-gray-400 mb-4" size={48} />
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
          Upload Documents
        </h3>
        <p className="text-gray-600 dark:text-gray-300 mb-4">
          Drag and drop files here, or click to browse
        </p>
        <input
          type="file"
          id="file-upload"
          className="hidden"
          onChange={handleFileInputChange}
          accept=".txt,.md,.json,.csv,.pdf,.html,.htm,.docx"
        />
        <label
          htmlFor="file-upload"
          className="inline-flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 cursor-pointer transition-colors"
        >
          <Upload size={20} />
          Choose File
        </label>
        <p className="text-sm text-gray-500 mt-2">
          Supported: TXT, MD, JSON, CSV, PDF, HTML, DOCX (max 10MB)
        </p>

        {/* Upload Progress */}
        {uploadProgress > 0 && uploadProgress < 100 && (
          <div className="mt-4">
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
              <div
                className="bg-blue-600 h-full transition-all duration-300"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Uploading... {uploadProgress}%
            </p>
          </div>
        )}
      </motion.div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search documents..."
          className="w-full pl-12 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-800 dark:text-white"
        />
      </div>

      {/* Documents List */}
      <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="animate-spin text-blue-600" size={32} />
          </div>
        ) : filteredDocuments.length > 0 ? (
          <div className="divide-y divide-gray-200 dark:divide-gray-700">
            {filteredDocuments.map((doc, index) => (
              <motion.div
                key={doc.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                className="flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
              >
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-lg">
                    <FileText className="text-blue-600 dark:text-blue-400" size={24} />
                  </div>
                  <div>
                    <h3 className="font-medium text-gray-900 dark:text-white">
                      {doc.filename}
                    </h3>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                      {doc.content_type || 'Unknown type'} • {new Date(doc.created_at).toLocaleDateString()}
                    </p>
                    {doc.indexed_at && (
                      <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                        Indexed {new Date(doc.indexed_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(doc.id)}
                  className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                >
                  <Trash2 size={20} />
                </button>
              </motion.div>
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <FileText className="mx-auto text-gray-400 mb-4" size={48} />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
              No documents yet
            </h3>
            <p className="text-gray-600 dark:text-gray-300">
              Upload your first document to get started
            </p>
          </div>
        )}
      </div>
    </div>
  );
};