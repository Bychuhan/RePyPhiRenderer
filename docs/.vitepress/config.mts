import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  srcDir: 'md',

  title: 'RePyPhiRenderer',
  description: '基于 Python 的 Phigros 谱面播放器 / 渲染器',
  lang: 'zh-Hans',
  base: '/pypr-docs/',
  cleanUrls: true,
  lastUpdated: true,

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
    ],

    outline: {
      level: [2, 6],
      label: "页面导航"
    },

    editLink: {
      pattern: 'https://github.com/Bychuhan/RePyPhiRenderer/edit/main/docs/:path',
      text: '在 GitHub 上编辑此页面'
    },

    lastUpdated: {
      text: '最后更新于',
      formatOptions: {
        dateStyle: 'medium',
        timeStyle: 'medium'
      }
    },

    docFooter: {
      prev: '上一页',
      next: '下一页'
    },

    darkModeSwitchLabel: '主题',
    lightModeSwitchTitle: '切换到浅色模式',
    darkModeSwitchTitle: '切换到深色模式',
    sidebarMenuLabel: '菜单',
    returnToTopLabel: '返回顶部',
  },
})
