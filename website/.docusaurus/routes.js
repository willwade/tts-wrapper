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
    component: ComponentCreator('/tts-wrapper/docs', 'bd4'),
    routes: [
      {
        path: '/tts-wrapper/docs',
        component: ComponentCreator('/tts-wrapper/docs', 'a60'),
        routes: [
          {
            path: '/tts-wrapper/docs',
            component: ComponentCreator('/tts-wrapper/docs', '8ad'),
            routes: [
              {
                path: '/tts-wrapper/docs/api/overview',
                component: ComponentCreator('/tts-wrapper/docs/api/overview', 'f9b'),
                exact: true
              },
              {
                path: '/tts-wrapper/docs/developer/adding-engines',
                component: ComponentCreator('/tts-wrapper/docs/developer/adding-engines', '277'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/developer/contributing',
                component: ComponentCreator('/tts-wrapper/docs/developer/contributing', '151'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/developer/overview',
                component: ComponentCreator('/tts-wrapper/docs/developer/overview', '3dd'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/developer/releases',
                component: ComponentCreator('/tts-wrapper/docs/developer/releases', '2eb'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/avsynth',
                component: ComponentCreator('/tts-wrapper/docs/engines/avsynth', '147'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/aws-polly',
                component: ComponentCreator('/tts-wrapper/docs/engines/aws-polly', '0f1'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/elevenlabs',
                component: ComponentCreator('/tts-wrapper/docs/engines/elevenlabs', '79c'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/espeak',
                component: ComponentCreator('/tts-wrapper/docs/engines/espeak', '8fa'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/google-cloud',
                component: ComponentCreator('/tts-wrapper/docs/engines/google-cloud', '507'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/googletrans',
                component: ComponentCreator('/tts-wrapper/docs/engines/googletrans', '20d'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/ibm-watson',
                component: ComponentCreator('/tts-wrapper/docs/engines/ibm-watson', '19a'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/microsoft-azure',
                component: ComponentCreator('/tts-wrapper/docs/engines/microsoft-azure', '9c7'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/overview',
                component: ComponentCreator('/tts-wrapper/docs/engines/overview', 'e81'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/playht',
                component: ComponentCreator('/tts-wrapper/docs/engines/playht', 'e75'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/sapi',
                component: ComponentCreator('/tts-wrapper/docs/engines/sapi', 'f82'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/sherpaonnx',
                component: ComponentCreator('/tts-wrapper/docs/engines/sherpaonnx', 'd4c'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/engines/witai',
                component: ComponentCreator('/tts-wrapper/docs/engines/witai', '049'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/guides/audio-control',
                component: ComponentCreator('/tts-wrapper/docs/guides/audio-control', '01d'),
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
                path: '/tts-wrapper/docs/guides/callbacks',
                component: ComponentCreator('/tts-wrapper/docs/guides/callbacks', '05e'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/guides/ssml',
                component: ComponentCreator('/tts-wrapper/docs/guides/ssml', '717'),
                exact: true,
                sidebar: "docs"
              },
              {
                path: '/tts-wrapper/docs/guides/streaming',
                component: ComponentCreator('/tts-wrapper/docs/guides/streaming', '324'),
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
              }
            ]
          }
        ]
      }
    ]
  },
  {
    path: '/tts-wrapper/',
    component: ComponentCreator('/tts-wrapper/', '61d'),
    exact: true
  },
  {
    path: '*',
    component: ComponentCreator('*'),
  },
];
