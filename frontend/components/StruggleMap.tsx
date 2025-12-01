'use client';

import React, { useState, useEffect } from 'react';
import { Users } from 'lucide-react';
import type { PeerNode, StruggleMapCluster } from '@/lib/types/api';
import { apiClient } from '@/lib/api/client';
import { useSessionStore } from '@/lib/stores/sessionStore';

export const StruggleMap: React.FC = () => {
  const { userId } = useSessionStore();
  const [nodes, setNodes] = useState<PeerNode[]>([]);
  const [clusters, setClusters] = useState<StruggleMapCluster[]>([]);
  const [hoveredCluster, setHoveredCluster] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadStruggleMap = async () => {
      if (!userId) {
        setLoading(false);
        return;
      }

      try {
        // Call the real API endpoint using apiClient
        const data = await apiClient.getStruggleMap(userId);
        setNodes(data.nodes || []);
        setClusters(data.clusters || []);
      } catch (error) {
        console.error('Failed to load struggle map:', error);
        // Fallback to empty map on error
        setNodes([]);
        setClusters([]);
      } finally {
        setLoading(false);
      }
    };

    loadStruggleMap();
  }, [userId]);

  if (loading) {
    return (
      <div className="relative w-full h-64 bg-stone-50 rounded-3xl overflow-hidden border border-stone-100 shadow-inner flex items-center justify-center">
        <div className="text-stone-400">Loading struggle map...</div>
      </div>
    );
  }

  return (
    <div className="relative w-full h-64 bg-gradient-to-br from-stone-50 via-purple-50/30 to-blue-50/30 rounded-3xl overflow-hidden border border-stone-200/50 shadow-lg group">
      {/* Background Pattern */}
      <div
        className="absolute inset-0 opacity-[0.03]"
        style={{
          backgroundImage: 'radial-gradient(circle, #5B4BFF 1px, transparent 1px)',
          backgroundSize: '24px 24px',
        }}
      />
      
      {/* Gradient Overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-transparent via-purple-500/5 to-blue-500/5 pointer-events-none" />

      {/* Header */}
      <div className="absolute top-3 left-3 z-10 bg-white/80 backdrop-blur-sm px-3 py-1.5 rounded-lg shadow-sm border border-stone-200/50">
        <h3 className="font-bold text-stone-800 flex items-center gap-2 text-sm">
          <Users size={14} className="text-purple-600" /> Struggle Map
        </h3>
        <p className="text-[10px] text-stone-500 mt-0.5">
          Peers with similar research journeys
        </p>
      </div>

      {/* Cluster Labels - Always visible but subtle, highlighted on hover */}
      {clusters.map((cluster) => (
        <div
          key={cluster.id}
          className="absolute transition-all duration-500 ease-out z-20"
          style={{
            left: `${cluster.center_x}%`,
            top: `${cluster.center_y}%`,
            transform: 'translate(-50%, -50%)',
          }}
          onMouseEnter={() => setHoveredCluster(cluster.id)}
          onMouseLeave={() => setHoveredCluster(null)}
        >
          <div
            className={`px-3 py-1.5 rounded-full text-xs font-semibold text-white shadow-xl backdrop-blur-sm transition-all duration-300 whitespace-nowrap ${
              hoveredCluster === cluster.id 
                ? 'opacity-100 scale-110 z-30' 
                : 'opacity-60 scale-100'
            }`}
            style={{ 
              backgroundColor: cluster.color,
              boxShadow: hoveredCluster === cluster.id 
                ? `0 4px 20px ${cluster.color}40` 
                : `0 2px 8px ${cluster.color}30`
            }}
          >
            {cluster.semantic_label}
          </div>
        </div>
      ))}

      {/* Nodes with improved styling */}
      {nodes.map((node, index) => (
        <div
          key={`${node.id}-${index}-${node.x}-${node.y}`}
          className="absolute rounded-full cursor-pointer transition-all duration-500 ease-out flex items-center justify-center group/node"
          style={{
            left: `${node.x}%`,
            top: `${node.y}%`,
            width: `${node.size}px`,
            height: `${node.size}px`,
            backgroundColor: node.color,
            opacity: hoveredCluster !== null && node.cluster_id !== hoveredCluster ? 0.2 : 0.85,
            transform: hoveredCluster === node.cluster_id ? 'scale(1.15)' : 'scale(1)',
            boxShadow: hoveredCluster === node.cluster_id 
              ? `0 4px 16px ${node.color}50, 0 0 0 2px ${node.color}20`
              : `0 2px 8px ${node.color}30`,
            zIndex: hoveredCluster === node.cluster_id ? 25 : 10,
          }}
          title={node.struggle}
          onMouseEnter={() => {
            if (node.cluster_id !== undefined) {
              setHoveredCluster(node.cluster_id);
            }
          }}
          onMouseLeave={() => setHoveredCluster(null)}
        >
          {/* Inner glow effect */}
          <div 
            className="absolute inset-0 rounded-full opacity-30"
            style={{
              background: `radial-gradient(circle at 30% 30%, white, transparent 70%)`,
            }}
          />
          {/* Center dot */}
          <div 
            className="w-1.5 h-1.5 bg-white rounded-full opacity-80 shadow-sm"
            style={{
              boxShadow: '0 0 4px rgba(255,255,255,0.8)',
            }}
          />
        </div>
      ))}

      {/* "You are here" indicator - improved */}
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-40 h-40 bg-gradient-to-r from-indigo-500/10 via-purple-500/10 to-blue-500/10 rounded-full animate-pulse pointer-events-none" />
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-3 h-3 bg-gradient-to-br from-indigo-600 to-purple-600 border-2 border-white rounded-full shadow-2xl z-30 ring-2 ring-indigo-200/50" />
      <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 translate-y-5 bg-gradient-to-r from-indigo-600 to-purple-600 text-white px-2.5 py-1 rounded-md text-[10px] font-bold shadow-lg whitespace-nowrap z-30 backdrop-blur-sm">
        You
      </div>
    </div>
  );
};


