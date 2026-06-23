import { create } from "zustand"

interface UIState {
  sidebarOpen: boolean
  commandPaletteOpen: boolean
  theme: "light" | "dark"
  toggleSidebar: () => void
  toggleCommandPalette: () => void
  toggleTheme: () => void
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  commandPaletteOpen: false,
  theme: "dark",
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  toggleCommandPalette: () => set((s) => ({ commandPaletteOpen: !s.commandPaletteOpen })),
  toggleTheme: () =>
    set((s) => {
      const next = s.theme === "dark" ? "light" : "dark"
      document.documentElement.classList.toggle("dark", next === "dark")
      return { theme: next }
    }),
}))
