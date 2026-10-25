import { useId } from 'react';

const source = '/branding/sigapi-logo.png';

/** Frame the original artwork; only remove the paper background from the horizontal lockup. */
export function BrandLogo({ stacked = false }: { stacked?: boolean }) {
  const paperFilterId = useId();
  if (stacked) {
    return (
      <svg className="brand-logo brand-logo-stacked" viewBox="427 364 1651 1707" width="72" height="74" role="img" aria-label="Logo SIGAPI">
        <image href={source} width="2508" height="2508" />
      </svg>
    );
  }

  return (
    <svg className="brand-logo brand-logo-horizontal" viewBox="0 0 160 54" width="160" height="54" role="img" aria-label="Logo SIGAPI">
      <defs>
        <filter id={paperFilterId} colorInterpolationFilters="sRGB">
          {/* RGB stays unchanged; the blue channel keys the light paper out of alpha. */}
          <feColorMatrix type="matrix" values="1 0 0 0 0 0 1 0 0 0 0 0 1 0 0 0 0 -1.6 0 1.5" />
        </filter>
      </defs>
      <svg x="0" y="0" width="37" height="54" viewBox="827 376 888 1291" overflow="hidden">
        <image href={source} width="2508" height="2508" filter={`url(#${paperFilterId})`} />
      </svg>
      <svg x="49" y="16" width="111" height="22" viewBox="439 1742 1627 317" overflow="hidden">
        <image href={source} width="2508" height="2508" filter={`url(#${paperFilterId})`} />
      </svg>
    </svg>
  );
}
