import { Github, Twitter, Mail } from 'lucide-react'

export default function About() {
    return (
        <main className="min-h-screen bg-background relative overflow-hidden pt-32 pb-20">
            <div className="container mx-auto px-6 max-w-4xl relative z-10">

                <div className="glass rounded-3xl p-12 border border-white/10 text-center space-y-8">
                    <div className="w-24 h-24 bg-primary/20 rounded-full mx-auto flex items-center justify-center border border-primary/50 text-4xl mb-6">
                        🛡️
                    </div>

                    <h1 className="text-5xl font-bold text-white">About Shield.AI</h1>

                    <p className="text-xl text-gray-400 leading-relaxed">
                        We are a collective of privacy advocates and AI researchers dedicated to protecting human creativity in the age of generative AI.
                    </p>

                    <div className="h-px bg-white/10 w-1/2 mx-auto my-12" />

                    <div className="space-y-6">
                        <h2 className="text-2xl font-bold text-white">Our Mission</h2>
                        <p className="text-gray-400">
                            To provide accessible, state-of-the-art tools for artists, photographers, and creators to safeguard their intellectual property functionality against unauthorized scraping and model training.
                        </p>
                    </div>

                    <div className="space-y-6 pt-12">
                        <h2 className="text-2xl font-bold text-white">Contact</h2>
                        <div className="flex justify-center space-x-6">
                            <SocialLink icon={Github} label="GitHub" />
                            <SocialLink icon={Twitter} label="Twitter" />
                            <SocialLink icon={Mail} label="Email" />
                        </div>
                    </div>
                </div>

            </div>
        </main>
    )
}

function SocialLink({ icon: Icon, label }: any) {
    return (
        <a href="#" className="p-3 bg-white/5 rounded-xl hover:bg-white/10 hover:text-primary transition-all text-gray-400">
            <Icon className="w-6 h-6" />
        </a>
    )
}
