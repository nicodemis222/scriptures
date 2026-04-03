import { useState, useEffect } from 'react';
import { listBundles, getVolumeStats } from '../hooks/useScriptures';
import type { BundleInfo, VolumeStat } from '../types/scriptures';

interface AssetManagerProps {
  onClose: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function AssetManager({ onClose }: AssetManagerProps) {
  const [bundles, setBundles] = useState<BundleInfo[]>([]);
  const [stats, setStats] = useState<VolumeStat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [bundleData, volumeStats] = await Promise.all([
          listBundles(),
          getVolumeStats(),
        ]);
        if (!cancelled) {
          setBundles(bundleData.bundles);
          setStats(volumeStats);
        }
      } catch {
        // Backend may not be running
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => { cancelled = true; };
  }, []);

  const getStatForBundle = (bundle: BundleInfo): VolumeStat | undefined => {
    return stats.find((s) => s.abbreviation === bundle.id);
  };

  const totalVerses = stats.reduce((sum, s) => sum + s.verse_count, 0);
  const totalBooks = stats.reduce((sum, s) => sum + s.book_count, 0);

  return (
    <div className="asset-manager">
      <div className="asset-manager-header">
        <h2 className="asset-manager-title">Scripture Library</h2>
        <button className="asset-manager-close" onClick={onClose}>
          &times;
        </button>
      </div>

      <p className="asset-manager-desc">
        All scripture volumes are bundled with the application for offline access.
        {!loading && stats.length > 0 && (
          <> Currently {totalVerses.toLocaleString()} verses across {totalBooks} books.</>
        )}
      </p>

      {loading ? (
        <div className="asset-manager-loading">Loading volumes...</div>
      ) : bundles.length === 0 ? (
        <div className="asset-manager-empty">
          No volume information available. The backend may not be running.
        </div>
      ) : (
        <div className="asset-manager-grid">
          {bundles.map((bundle) => {
            const stat = getStatForBundle(bundle);
            return (
              <div key={bundle.id} className="asset-card ornamental-card">
                <div className="asset-card-header">
                  <span className="asset-card-title">{bundle.name}</span>
                  {bundle.installed && (
                    <span className="asset-card-badge">Installed</span>
                  )}
                </div>
                {stat && (
                  <p className="asset-card-desc">
                    {stat.book_count} books &middot; {stat.chapter_count.toLocaleString()} chapters &middot; {stat.verse_count.toLocaleString()} verses
                  </p>
                )}
                <div className="asset-card-meta">
                  <span className="asset-card-abbr">{bundle.id}</span>
                  {' '}
                  <span>{formatBytes(bundle.size_bytes)}</span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      <div className="asset-manager-footer">
        <button className="asset-download-all-btn" disabled>
          All Volumes Installed
        </button>
      </div>
    </div>
  );
}
