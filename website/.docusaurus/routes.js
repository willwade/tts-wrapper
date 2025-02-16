import React from 'react';
import ComponentCreator from '@docusaurus/ComponentCreator';

export default [
  {
    path: '/tts-wrapper/__docusaurus/debug',
    component: ComponentCreator('/tts-wrapper/__docusaurus/debug', 'c5a'),
    exact: true
  },
  {
    path: '/tts-wrapper/__docusaurus/debug/config',
    component: ComponentCreator('/tts-wrapper/__docusaurus/debug/config', 'aed'),
    exact: true
  },
  {
    path: '/tts-wrapper/__docusaurus/debug/content',
    component: ComponentCreator('/tts-wrapper/__docusaurus/debug/content', 'a42'),
    exact: true
  },
  {
    path: '/tts-wrapper/__docusaurus/debug/globalData',
    component: ComponentCreator('/tts-wrapper/__docusaurus/debug/globalData', '4d3'),
    exact: true
  },
  {
    path: '/tts-wrapper/__docusaurus/debug/metadata',
    component: ComponentCreator('/tts-wrapper/__docusaurus/debug/metadata', '371'),
    exact: true
  },
  {
    path: '/tts-wrapper/__docusaurus/debug/registry',
    component: ComponentCreator('/tts-wrapper/__docusaurus/debug/registry', '116'),
    exact: true
  },
  {
    path: '/tts-wrapper/__docusaurus/debug/routes',
    component: ComponentCreator('/tts-wrapper/__docusaurus/debug/routes', 'e92'),
    exact: true
  },
  {
    path: '/tts-wrapper/docs',
    component: ComponentCreator('/tts-wrapper/docs', 'a11'),
    routes: [
      {
        path: '/tts-wrapper/docs',
        component: ComponentCreator('/tts-wrapper/docs', 'aef'),
        routes: [
          {
            path: '/tts-wrapper/docs',
            component: ComponentCreator('/tts-wrapper/docs', 'adf'),
            routes: [
              {
                path: '/tts-wrapper/docs/api/overview',
                component: ComponentCreator('/tts-wrapper/docs/api/overview', '23c'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/guides/basic-usage',
                component: ComponentCreator('/tts-wrapper/docs/guides/basic-usage', 'a92'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/installation',
                component: ComponentCreator('/tts-wrapper/docs/installation', 'a07'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/intro',
                component: ComponentCreator('/tts-wrapper/docs/intro', '63e'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/quickstart',
                component: ComponentCreator('/tts-wrapper/docs/quickstart', 'da6'),
                exact: true,
                sidebar: "docs"
              }
            ]
          }
        ]
      }
    ]
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
