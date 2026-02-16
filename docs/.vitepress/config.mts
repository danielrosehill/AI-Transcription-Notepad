import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'AI Transcription Notepad',
  description: 'Desktop app for voice recording with AI-powered transcription and cleanup',
  base: '/AI-Transcription-Notepad/',
  srcExclude: ['documentation/**', 'version-releases/**'],

  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/AI-Transcription-Notepad/icon.png' }]
  ],

  themeConfig: {
    logo: '/icon.png',

    nav: [
      { text: 'Guide', link: '/guide/installation' },
      { text: 'Reference', link: '/reference/models' },
      {
        text: 'Download',
        items: [
          { text: 'GitHub Releases', link: 'https://github.com/danielrosehill/AI-Transcription-Notepad/releases' },
          { text: 'User Manual (PDF)', link: '/manuals/Voice-Notepad-User-Manual-v3.pdf' }
        ]
      }
    ],

    sidebar: {
      '/guide/': [
        {
          text: 'Getting Started',
          items: [
            { text: 'Installation', link: '/guide/installation' },
            { text: 'Configuration', link: '/guide/configuration' },
            { text: 'Hotkey Setup', link: '/guide/hotkey-setup' },
            { text: 'Text Injection', link: '/guide/text-injection' }
          ]
        },
        {
          text: 'Using the App',
          items: [
            { text: 'Keyboard Shortcuts', link: '/guide/shortcuts' },
            { text: 'Audio Feedback', link: '/guide/audio-feedback' },
            { text: 'Translation Mode', link: '/guide/translation' },
            { text: 'File Transcription', link: '/guide/file-transcription' },
            { text: 'Semantic Search', link: '/guide/semantic-search' },
            { text: 'Cost Tracking', link: '/guide/cost-tracking' },
            { text: 'Troubleshooting', link: '/guide/troubleshooting' }
          ]
        }
      ],
      '/reference/': [
        {
          text: 'Technical Reference',
          items: [
            { text: 'Supported Models', link: '/reference/models' },
            { text: 'Audio Pipeline', link: '/reference/audio-pipeline' },
            { text: 'Prompt System', link: '/reference/prompt-concatenation' },
            { text: 'Technology Stack', link: '/reference/stack' },
            { text: 'Multimodal vs ASR', link: '/reference/multimodal-vs-asr' }
          ]
        }
      ]
    },

    socialLinks: [
      { icon: 'github', link: 'https://github.com/danielrosehill/AI-Transcription-Notepad' }
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2024-2026 Daniel Rosehill'
    },

    search: {
      provider: 'local'
    },

    editLink: {
      pattern: 'https://github.com/danielrosehill/AI-Transcription-Notepad/edit/main/docs/:path',
      text: 'Edit this page on GitHub'
    }
  }
})
