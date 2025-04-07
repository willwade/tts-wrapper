/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    {
      type: 'category',
      label: 'Getting Started',
      items: ['intro', 'installation'],
    },
    {
      type: 'category',
      label: 'Guides',
      items: [
        'guides/basic-usage',
        'guides/voices',
        'guides/ssml',
        'guides/audio-control',
        'guides/streaming',
        'guides/callbacks',
      ],
    },
    {
      type: 'category',
      label: 'Engines',
      items: [
        'engines/overview',
        'engines/aws-polly',
        'engines/google-cloud',
        'engines/microsoft-azure',
        'engines/ibm-watson',
        'engines/openai',
        'engines/elevenlabs',
        'engines/playht',
        'engines/witai',
        'engines/espeak',
        'engines/sapi',
        'engines/avsynth',
        'engines/googletrans',
        'engines/sherpaonnx',
      ],
    },
    {
      type: 'category',
      label: 'Developer Guide',
      items: [
        'developer/overview',
        'developer/adding-engines',
        'developer/releases',
        'developer/contributing',
      ],
    },
  ],
};

module.exports = sidebars;