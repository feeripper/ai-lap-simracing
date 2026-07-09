/** @type {import('@docusaurus/plugin-content-docs').SidebarsConfig} */
const sidebars = {
  tutorialSidebar: [
    'intro',
    {
      type: 'category',
      label: 'Começando',
      items: ['getting-started'],
    },
    {
      type: 'category',
      label: 'Uso',
      items: ['local-usage', 'reference-laps', 'cli-commands', 'mvp-web-flow'],
    },
    {
      type: 'category',
      label: 'Referência',
      items: ['telemetry-csv-format', 'architecture'],
    },
    {
      type: 'category',
      label: 'Integrações',
      items: ['garage61-spike'],
    },
    {
      type: 'category',
      label: 'Sobre',
      items: ['roadmap', 'product-roadmap'],
    },
  ],
};

module.exports = sidebars;
