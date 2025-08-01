/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{vue,js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: '#9CC932', // 绿色作为主色调
        secondary: '#f1f5f9', // 浅灰作为次要背景色
        neutral: '#64748b', // 中性灰用于文本
        placeholder: '#94a3b8', // 专门用于占位符的颜色
        light: '#f8fafc', // 浅色背景
        border: '#e2e8f0', // 边框颜色
        speaker1: '#9CC932', // 张小明-绿色
        speaker2: '#3B82F6', // 李华-蓝色
        speaker3: '#F97316', // 王芳-橙色
        export: '#8B5CF6', // 紫色用于导出按钮
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
} 