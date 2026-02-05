import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  srcDir: "md",

  title: "RePyPhiRenderer",
  description: "基于 Python 的 Phigros 谱面播放器 / 渲染器",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: '主页', link: '/' },
    ],

    sidebar: [
      {
        text: '基础',
        items: [
          { text: '快速开始', link: '/quick-start' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/Bychuhan/RePyPhiRenderer' }
    ]
  }
})
