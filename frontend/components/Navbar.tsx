'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Shield, Home, Info, Cpu } from 'lucide-react'

export default function Navbar() {
    const pathname = usePathname()

    const isActive = (path: string) => pathname === path

    return (
        <nav className="fixed top-0 left-0 right-0 z-50 px-6 py-4">
            <div className="max-w-7xl mx-auto">
                <div className="glass rounded-full px-6 py-3 flex items-center justify-between border border-white/10 bg-black/40 backdrop-blur-md">

                    {/* Logo */}
                    <Link href="/" className="flex items-center space-x-2 group">
                        <Shield className="w-6 h-6 text-primary group-hover:drop-shadow-[0_0_8px_rgba(255,255,0,0.5)] transition-all" />
                        <span className="font-bold text-white tracking-wide">SHIELD<span className="text-primary">.AI</span></span>
                    </Link>

                    {/* Navigation Links */}
                    <div className="hidden md:flex items-center space-x-1">
                        <NavLink href="/" icon={Home} label="Home" active={isActive('/')} />
                        <NavLink href="/technology" icon={Cpu} label="Technology" active={isActive('/technology')} />
                        <NavLink href="/about" icon={Info} label="About" active={isActive('/about')} />
                    </div>

                    {/* Mobile Menu Button (Placeholder for now, keeping it simple) */}
                    <div className="md:hidden">
                        {/* Can add mobile menu later if requested */}
                    </div>

                    {/* Status Indicator */}
                    <div className="flex items-center space-x-2">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        <span className="text-xs font-mono text-gray-400">SYSTEM ONLINE</span>
                    </div>
                </div>
            </div>
        </nav>
    )
}

function NavLink({ href, icon: Icon, label, active }: { href: string, icon: any, label: string, active: boolean }) {
    return (
        <Link
            href={href}
            className={`
        flex items-center space-x-2 px-4 py-2 rounded-full transition-all duration-300
        ${active
                    ? 'bg-white/10 text-white shadow-[0_0_15px_rgba(255,255,255,0.1)]'
                    : 'text-gray-400 hover:text-white hover:bg-white/5'}
      `}
        >
            <Icon className={`w-4 h-4 ${active ? 'text-primary' : ''}`} />
            <span className="text-sm font-medium">{label}</span>
        </Link>
    )
}
