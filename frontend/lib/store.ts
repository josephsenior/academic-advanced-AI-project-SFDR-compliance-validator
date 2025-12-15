import { create } from "zustand"
import type { SeverityFilter, SortOption } from "./types"

interface UIState {
  darkMode: boolean
  toggleDarkMode: () => void

  // Filters
  selectedCategories: string[]
  toggleCategory: (category: string) => void
  setCategories: (categories: string[]) => void

  selectedSeverities: SeverityFilter[]
  toggleSeverity: (severity: SeverityFilter) => void

  selectedSlide: number | null
  setSelectedSlide: (slide: number | null) => void

  // Search & Sort
  searchQuery: string
  setSearchQuery: (query: string) => void

  sortOption: SortOption
  setSortOption: (option: SortOption) => void

  // Reset
  resetFilters: () => void
}

export const useUIStore = create<UIState>((set) => ({
  darkMode: true,
  toggleDarkMode: () => set((state) => ({ darkMode: !state.darkMode })),

  selectedCategories: [],
  toggleCategory: (category) =>
    set((state) => ({
      selectedCategories: state.selectedCategories.includes(category)
        ? state.selectedCategories.filter((c) => c !== category)
        : [...state.selectedCategories, category],
    })),
  setCategories: (categories) => set({ selectedCategories: categories }),

  selectedSeverities: ["critical", "high", "medium", "low"],
  toggleSeverity: (severity) =>
    set((state) => ({
      selectedSeverities: state.selectedSeverities.includes(severity)
        ? state.selectedSeverities.filter((s) => s !== severity)
        : [...state.selectedSeverities, severity],
    })),

  selectedSlide: null,
  setSelectedSlide: (slide) => set({ selectedSlide: slide }),

  searchQuery: "",
  setSearchQuery: (query) => set({ searchQuery: query }),

  sortOption: "severity",
  setSortOption: (option) => set({ sortOption: option }),

  resetFilters: () =>
    set({
      selectedCategories: [],
      selectedSeverities: ["critical", "high", "medium", "low"],
      selectedSlide: null,
      searchQuery: "",
      sortOption: "severity",
    }),
}))
