import React, { useMemo } from 'react';
import { Box, Typography, Chip, Paper } from '@mui/material';

/**
 * AttackGraph – renders an SVG-based directed graph of infrastructure resources
 * with edges showing relationships and attack paths highlighted.
 */

const NODE_W = 160;
const NODE_H = 72;
const LAYER_GAP_X = 220;
const NODE_GAP_Y = 100;
const PAD = 40;

// resource type → layer priority (lower = farther left / entry)
const LAYER_PRIORITY = {
  aws_security_group: 0,
  aws_instance: 1,
  aws_lb: 1,
  aws_alb: 1,
  aws_s3_bucket: 2,
  aws_db_instance: 2,
  aws_rds_cluster: 2,
  aws_lambda_function: 2,
  aws_iam_role: 1,
  aws_iam_policy: 1,
};

function getLayerForType(type) {
  if (!type) return 1;
  const t = type.toLowerCase();
  for (const [k, v] of Object.entries(LAYER_PRIORITY)) {
    if (t.includes(k) || t.includes(k.replace('aws_', ''))) return v;
  }
  return 1;
}

function layoutNodes(nodes, edges) {
  // Assign layers
  const layerMap = {};
  nodes.forEach((n) => {
    const layer = n.is_entry_point ? 0 : n.is_target ? 2 : getLayerForType(n.type);
    layerMap[n.id || n.label] = layer;
  });

  // Group by layer
  const layers = {};
  nodes.forEach((n) => {
    const l = layerMap[n.id || n.label] ?? 1;
    if (!layers[l]) layers[l] = [];
    layers[l].push(n);
  });

  const sortedLayers = Object.keys(layers).map(Number).sort((a, b) => a - b);
  const positions = {};

  sortedLayers.forEach((layerIdx, col) => {
    const layerNodes = layers[layerIdx];
    const totalH = layerNodes.length * NODE_H + (layerNodes.length - 1) * (NODE_GAP_Y - NODE_H);
    const startY = PAD;
    layerNodes.forEach((n, row) => {
      positions[n.id || n.label] = {
        x: PAD + col * LAYER_GAP_X,
        y: startY + row * NODE_GAP_Y,
      };
    });
  });

  const maxCol = sortedLayers.length;
  const maxRow = Math.max(...Object.values(layers).map((l) => l.length), 1);
  const svgW = PAD * 2 + maxCol * LAYER_GAP_X;
  const svgH = PAD * 2 + maxRow * NODE_GAP_Y;

  return { positions, svgW, svgH };
}

function NodeRect({ node, x, y, isOnAttackPath }) {
  const fill = node.is_entry_point
    ? '#3a1b1b'
    : node.is_target
    ? '#3a2e1b'
    : isOnAttackPath
    ? '#2e2a1b'
    : '#132f4c';
  const stroke = node.is_entry_point
    ? '#ef5350'
    : node.is_target
    ? '#ffa726'
    : isOnAttackPath
    ? '#ffb74d'
    : '#1e4976';
  const strokeW = node.is_entry_point || node.is_target ? 2.5 : 1.5;

  const label = (node.label || node.id || '').replace(/^aws_/, '');
  const typeName = (node.type || '').replace(/^aws_/, '');

  return (
    <g>
      <rect
        x={x}
        y={y}
        width={NODE_W}
        height={NODE_H}
        rx={10}
        ry={10}
        fill={fill}
        stroke={stroke}
        strokeWidth={strokeW}
        style={{ filter: node.is_entry_point || node.is_target ? 'drop-shadow(0 2px 4px rgba(0,0,0,0.15))' : 'none' }}
      />
      {/* Label */}
      <text x={x + NODE_W / 2} y={y + 22} textAnchor="middle" fontSize={11} fontWeight="bold" fontFamily="monospace" fill="#e0e0e0">
        {label.length > 22 ? label.slice(0, 20) + '…' : label}
      </text>
      {/* Type */}
      <text x={x + NODE_W / 2} y={y + 38} textAnchor="middle" fontSize={9} fill="#90a4ae" fontFamily="sans-serif">
        {typeName}
      </text>
      {/* Badges row */}
      {(node.is_entry_point || node.is_target || node.vulnerabilities > 0) && (
        <g>
          {node.is_entry_point && (
            <>
              <rect x={x + 8} y={y + 48} width={42} height={16} rx={8} fill="#ef5350" />
              <text x={x + 29} y={y + 60} textAnchor="middle" fontSize={8} fill="white" fontWeight="bold">ENTRY</text>
            </>
          )}
          {node.is_target && (
            <>
              <rect x={x + (node.is_entry_point ? 56 : 8)} y={y + 48} width={52} height={16} rx={8} fill="#ffa726" />
              <text x={x + (node.is_entry_point ? 82 : 34)} y={y + 60} textAnchor="middle" fontSize={8} fill="white" fontWeight="bold">TARGET</text>
            </>
          )}
          {node.vulnerabilities > 0 && (
            <>
              <rect x={x + NODE_W - 52} y={y + 48} width={44} height={16} rx={8} fill={node.max_severity === 'CRITICAL' ? '#ef5350' : '#ffa726'} />
              <text x={x + NODE_W - 30} y={y + 60} textAnchor="middle" fontSize={8} fill="white" fontWeight="bold">{node.vulnerabilities} vuln</text>
            </>
          )}
        </g>
      )}
    </g>
  );
}

function EdgeLine({ x1, y1, x2, y2, isAttackPath, label }) {
  const midX = (x1 + x2) / 2;
  const midY = (y1 + y2) / 2;
  // Bezier curve control points for smooth edges
  const cx1 = x1 + (x2 - x1) * 0.4;
  const cy1 = y1;
  const cx2 = x1 + (x2 - x1) * 0.6;
  const cy2 = y2;

  return (
    <g>
      <path
        d={`M${x1},${y1} C${cx1},${cy1} ${cx2},${cy2} ${x2},${y2}`}
        fill="none"
        stroke={isAttackPath ? '#ef5350' : '#1e4976'}
        strokeWidth={isAttackPath ? 2.5 : 1.2}
        strokeDasharray={isAttackPath ? 'none' : '6,3'}
        markerEnd={isAttackPath ? 'url(#arrowRed)' : 'url(#arrowGrey)'}
      />
      {label && (
        <text x={midX} y={midY - 6} textAnchor="middle" fontSize={8} fill="#90a4ae" fontFamily="sans-serif">
          {label}
        </text>
      )}
    </g>
  );
}

export default function AttackGraph({ graphData, attackPaths }) {
  const nodes = graphData?.nodes || [];
  const edges = graphData?.edges || [];

  // Determine which nodes are on any attack path
  const attackPathNodeIds = useMemo(() => {
    const ids = new Set();
    (attackPaths || []).forEach((p) => {
      (p.chain || []).forEach((c) => {
        ids.add(c.resource_name || c.resource);
      });
    });
    return ids;
  }, [attackPaths]);

  // Build edge set from attack paths for highlighting
  const attackEdgeSet = useMemo(() => {
    const s = new Set();
    (attackPaths || []).forEach((p) => {
      const chain = p.chain || [];
      for (let i = 0; i < chain.length - 1; i++) {
        const src = chain[i].resource_name || chain[i].resource;
        const tgt = chain[i + 1].resource_name || chain[i + 1].resource;
        s.add(`${src}→${tgt}`);
      }
    });
    return s;
  }, [attackPaths]);

  const { positions, svgW, svgH } = useMemo(() => layoutNodes(nodes, edges), [nodes, edges]);

  if (nodes.length === 0) return null;

  return (
    <Paper
      variant="outlined"
      sx={{
        p: 2,
        borderRadius: 2,
        bgcolor: '#0a1929',
        border: '1px solid',
        borderColor: 'rgba(255,255,255,0.08)',
        overflow: 'auto',
      }}
    >
      <Typography variant="subtitle1" fontWeight="bold" gutterBottom>
        Infrastructure Dependency Graph
      </Typography>
      <Box sx={{ overflow: 'auto', maxWidth: '100%' }}>
        <svg width={Math.max(svgW, 500)} height={Math.max(svgH, 200)} style={{ display: 'block' }}>
          <defs>
            <marker id="arrowRed" viewBox="0 0 10 7" refX="10" refY="3.5" markerWidth="8" markerHeight="6" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#ef5350" />
            </marker>
            <marker id="arrowGrey" viewBox="0 0 10 7" refX="10" refY="3.5" markerWidth="8" markerHeight="6" orient="auto">
              <polygon points="0 0, 10 3.5, 0 7" fill="#1e4976" />
            </marker>
          </defs>

          {/* Edges */}
          {edges.map((e, i) => {
            const srcPos = positions[e.source];
            const tgtPos = positions[e.target];
            if (!srcPos || !tgtPos) return null;
            const isAP = attackEdgeSet.has(`${e.source}→${e.target}`);
            return (
              <EdgeLine
                key={i}
                x1={srcPos.x + NODE_W}
                y1={srcPos.y + NODE_H / 2}
                x2={tgtPos.x}
                y2={tgtPos.y + NODE_H / 2}
                isAttackPath={isAP}
                label={e.relationship}
              />
            );
          })}

          {/* Attack path edges not in explicit edges list */}
          {(attackPaths || []).map((p, pi) =>
            (p.chain || []).slice(0, -1).map((c, ci) => {
              const src = c.resource_name || c.resource;
              const tgt = (p.chain[ci + 1].resource_name || p.chain[ci + 1].resource);
              // skip if already rendered via edges
              const alreadyRendered = edges.some(
                (e) => e.source === src && e.target === tgt
              );
              if (alreadyRendered) return null;
              const srcPos = positions[src];
              const tgtPos = positions[tgt];
              if (!srcPos || !tgtPos) return null;
              return (
                <EdgeLine
                  key={`ap-${pi}-${ci}`}
                  x1={srcPos.x + NODE_W}
                  y1={srcPos.y + NODE_H / 2}
                  x2={tgtPos.x}
                  y2={tgtPos.y + NODE_H / 2}
                  isAttackPath={true}
                  label={p.chain[ci + 1]?.relationship}
                />
              );
            })
          )}

          {/* Nodes */}
          {nodes.map((n, i) => {
            const pos = positions[n.id || n.label];
            if (!pos) return null;
            return (
              <NodeRect
                key={i}
                node={n}
                x={pos.x}
                y={pos.y}
                isOnAttackPath={attackPathNodeIds.has(n.id || n.label)}
              />
            );
          })}
        </svg>
      </Box>

      {/* Legend */}
      <Box sx={{ display: 'flex', gap: 2.5, mt: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 14, height: 14, borderRadius: 1, bgcolor: '#3a1b1b', border: '2px solid #ef5350' }} />
          <Typography variant="caption">Entry Point</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 14, height: 14, borderRadius: 1, bgcolor: '#3a2e1b', border: '2px solid #ffa726' }} />
          <Typography variant="caption">High-Value Target</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 14, height: 14, borderRadius: 1, bgcolor: '#132f4c', border: '1.5px solid #1e4976' }} />
          <Typography variant="caption">Resource</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 24, height: 0, borderTop: '2.5px solid #ef5350' }} />
          <Typography variant="caption" sx={{ ml: 0.5 }}>Attack Path</Typography>
        </Box>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <Box sx={{ width: 24, height: 0, borderTop: '1.5px dashed #1e4976' }} />
          <Typography variant="caption" sx={{ ml: 0.5 }}>Dependency</Typography>
        </Box>
      </Box>
    </Paper>
  );
}
