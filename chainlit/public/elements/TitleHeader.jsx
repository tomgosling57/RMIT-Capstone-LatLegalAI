import { useEffect, useState } from 'react';

export default function TitleHeader() {
    // Props are globally injected by Chainlit — NOT as function arguments.
    // See: docs/chainlit/api-reference/elements/custom.md
    const [theme, setTheme] = useState(props?.theme || 'light');
    const [isNarrow, setIsNarrow] = useState(
        typeof window !== 'undefined' && window.matchMedia('(max-width: 499px)').matches
    );

    useEffect(() => {
        const html = document.documentElement;

        // Sync with DOM data-theme attribute (in case it differs from the server prop)
        const domTheme = html.getAttribute('data-theme');
        if (domTheme) {
            setTheme(domTheme);
        }

        // Watch for theme changes (user toggles dark/light mode)
        const observer = new MutationObserver(() => {
            const currentTheme = html.getAttribute('data-theme') || 'light';
            setTheme(currentTheme);
        });

        observer.observe(html, {
            attributes: true,
            attributeFilter: ['data-theme'],
        });

        return () => observer.disconnect();
    }, []);

    // Watch viewport width changes — hide the header when narrower than 500px
    useEffect(() => {
        const mq = window.matchMedia('(max-width: 500px)');
        const handler = (e) => setIsNarrow(e.matches);
        mq.addEventListener('change', handler);
        return () => mq.removeEventListener('change', handler);
    }, []);

    // Dynamically resolve the public URL relative to the Chainlit root path.
    // When served behind nginx at /chat/, window.location.pathname is "/chat/",
    // so we strip the trailing slash to construct "/chat/public/title_*.png".
    // When accessed directly at :8001, pathname is "/", basePath becomes "".
    const filename = theme === 'light' ? 'title_light.png' : 'title_dark.png';
    const src = '/chat/public/' + filename;


    return (
        <div
            id="title-header"
            className="fixed z-50"
            style={{
                right: '215px',
                top: '10px',
                display: isNarrow ? 'none' : 'block',
            }}
        >
            <img
                src={src}
                alt="LatLegal AI"
                className="title-header-logo"
                style={{ height: '20px', width: 'auto', display: 'block' }}
            />
        </div>
    );
}

