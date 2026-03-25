import { themes as prismThemes } from 'prism-react-renderer'

/** @type {import('@docusaurus/types').Config} */
const config = {
    title: 'Frontend Gitbook',
    tagline: '前端个人知识总结',
    favicon: 'img/favicon.ico',

    future: {
        v4: true,
    },

    url: 'https://yujiaming890321.github.io',
    baseUrl: '/frontend-gitbook/',

    organizationName: 'yujiaming890321',
    projectName: 'frontend-gitbook',

    onBrokenLinks: 'warn',
    onBrokenMarkdownLinks: 'warn',
    onBrokenAnchors: 'warn',

    i18n: {
        defaultLocale: 'zh-Hans',
        locales: ['zh-Hans'],
    },

    markdown: {
        format: 'md',
        hooks: {
            onBrokenMarkdownImages: 'warn',
        },
    },

    presets: [
        [
            'classic',
            /** @type {import('@docusaurus/preset-classic').Options} */
            ({
                docs: {
                    routeBasePath: '/',
                    sidebarPath: './sidebars.js',
                    editUrl:
                        'https://github.com/yujiaming890321/frontend-gitbook/tree/master/',
                    exclude: [
                        '**/*.js',
                        '**/*.jsx',
                        '**/*.ts',
                        '**/*.tsx',
                        '**/*.test.*',
                        '**/demo/**',
                        '**/Promise/**',
                        '**/ServiceWorker-demo/**',
                        '**/WebWorker-demo/**',
                        '**/node_modules/**',
                    ],
                },
                blog: false,
                theme: {
                    customCss: './src/css/custom.css',
                },
            }),
        ],
    ],

    themeConfig:
        /** @type {import('@docusaurus/preset-classic').ThemeConfig} */
        ({
            colorMode: {
                respectPrefersColorScheme: true,
            },
            navbar: {
                title: 'Frontend Gitbook',
                items: [
                    {
                        type: 'docSidebar',
                        sidebarId: 'mainSidebar',
                        position: 'left',
                        label: '文档',
                    },
                    {
                        href: 'https://github.com/yujiaming890321/frontend-gitbook',
                        label: 'GitHub',
                        position: 'right',
                    },
                ],
            },
            footer: {
                style: 'dark',
                copyright: `Copyright © ${new Date().getFullYear()} Frontend Gitbook. Built with Docusaurus.`,
            },
            prism: {
                theme: prismThemes.github,
                darkTheme: prismThemes.dracula,
            },
        }),
}

export default config
