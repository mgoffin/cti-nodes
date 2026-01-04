import { useState, useRef, useEffect } from 'react'

interface ComboboxProps {
  value: string
  onChange: (value: string) => void
  options: string[]
  placeholder?: string
  className?: string
  autoFocus?: boolean
  formatOption?: (option: string) => string
  onKeyDown?: (e: React.KeyboardEvent) => void
}

export default function Combobox({
  value,
  onChange,
  options,
  placeholder = 'Select or type...',
  className = '',
  autoFocus = false,
  formatOption,
  onKeyDown,
}: ComboboxProps) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Filter options based on input value
  const filteredOptions = value
    ? options.filter(opt => opt.toLowerCase().includes(value.toLowerCase()))
    : options

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (option: string) => {
    onChange(option)
    setIsOpen(false)
  }

  const handleInputKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setIsOpen(true)
    } else if (e.key === 'Escape') {
      setIsOpen(false)
    }
    onKeyDown?.(e)
  }

  const handleToggleDropdown = (e: React.MouseEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setIsOpen(prev => !prev)
  }

  const displayFormat = formatOption || ((s: string) => s)

  return (
    <div ref={containerRef} className={`relative ${className}`}>
      <div className="flex">
        <input
          ref={inputRef}
          type="text"
          value={value}
          onChange={(e) => {
            onChange(e.target.value)
            setIsOpen(true)
          }}
          onKeyDown={handleInputKeyDown}
          placeholder={placeholder}
          className="input w-full px-2 text-sm rounded-r-none border-r-0"
          autoFocus={autoFocus}
        />
        <button
          type="button"
          onMouseDown={handleToggleDropdown}
          className="input px-2 rounded-l-none border-l-0 hover:bg-slate-100 dark:hover:bg-slate-700 cursor-pointer"
          tabIndex={-1}
        >
          <svg
            className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {isOpen && filteredOptions.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 max-h-48 overflow-auto rounded-md combobox-dropdown border theme-border shadow-lg">
          {filteredOptions.map((option) => (
            <li key={option}>
              <button
                type="button"
                onMouseDown={(e) => {
                  e.preventDefault()
                  handleSelect(option)
                }}
                className={`w-full px-3 py-2 text-left text-sm theme-text-primary combobox-option ${
                  option === value ? 'combobox-option-selected' : ''
                }`}
              >
                {displayFormat(option)}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
