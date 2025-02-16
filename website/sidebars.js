/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  docs: [
    {
      type: 'category',
      label: 'Getting Started',
      items: ['intro', 'installation', 'quickstart'],
    },
    {
      type: 'category',
      label: 'Guides',
      items: [
        'guides/basic-usage',
      ],
    },
    {
      type: 'category',
      label: 'API Reference',
      items: [
        'api/overview',
      ],
    },
  ],
};

module.exports = sidebars; 