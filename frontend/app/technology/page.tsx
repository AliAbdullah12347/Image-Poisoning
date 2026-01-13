import { Layers, Zap, Lock, Eye, Server, ShieldCheck, Activity } from 'lucide-react'

export default function Technology() {
    return (
        <main className="min-h-screen bg-background relative overflow-hidden pt-32 pb-20">
            {/* Background Grid */}
            <div className="absolute inset-0 bg-grid-pattern bg-[length:30px_30px] opacity-[0.03] pointer-events-none" />

            <div className="container mx-auto px-6 max-w-6xl relative z-10">
                <div className="text-center mb-20">
                    <h1 className="text-5xl md:text-6xl font-bold text-white mb-6">
                        The <span className="text-primary">Technology</span>
                    </h1>
                    <p className="text-xl text-gray-400 max-w-3xl mx-auto">
                        Deep dive into our ensemble adversarial attack engine. We use industry-standard computer vision models to generate robust protection patterns.
                    </p>
                </div>

                {/* Core Models Section */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-24">
                    <ModelCard
                        title="VGG19"
                        desc="A 19-layer Convolutional Network. We target the deep feature layers to create high-level semantic confusion."
                        param="143M Parameters"
                        color="border-blue-500/50"
                        glow="shadow-[0_0_30px_-10px_rgba(59,130,246,0.3)]"
                    />
                    <ModelCard
                        title="ResNet50"
                        desc="Uses residual learning frames. We disrupt the skip connections, making the image unrecognizable to modern classifiers."
                        param="25M Parameters"
                        color="border-red-500/50"
                        glow="shadow-[0_0_30px_-10px_rgba(239,68,68,0.3)]"
                    />
                    <ModelCard
                        title="InceptionV3"
                        desc="Optimized for computational efficiency. Our attack specifically targets its localized feature extraction mechanism."
                        param="24M Parameters"
                        color="border-green-500/50"
                        glow="shadow-[0_0_30px_-10px_rgba(34,197,94,0.3)]"
                    />
                </div>

                {/* Technical Process */}
                <div className="glass rounded-3xl p-8 md:p-12 mb-20 border border-white/10">
                    <h2 className="text-3xl font-bold text-white mb-12 text-center">How The Attack Works</h2>

                    <div className="space-y-12">
                        <ProcessStep
                            number="01"
                            title="Gradient Calculation"
                            desc="We perform a backward pass through the neural networks, but instead of updating weights, we calculate the gradient of the loss with respect to the input pixels."
                            icon={Activity}
                        />
                        <ProcessStep
                            number="02"
                            title="Perturbation Generation"
                            desc="Using the Sign of the Gradient (FGSM/PGD), we generate a noise pattern that pushes the image towards a different classification boundary."
                            icon={Zap}
                        />
                        <ProcessStep
                            number="03"
                            title="Perceptual Locking"
                            desc="We simultaneously optimize a perceptual loss function (LPIPS) to ensure the noise remains invisible to the human eye, keeping pixel changes below a tight epsilon threshold."
                            icon={Lock}
                        />
                    </div>
                </div>
            </div>
        </main>
    )
}

function ModelCard({ title, desc, param, color, glow }: any) {
    return (
        <div className={`bg-surface/50 p-8 rounded-2xl border ${color} hover:border-white/40 transition-all group ${glow} hover:-translate-y-1`}>
            <div className="flex items-center justify-between mb-6">
                <Server className="w-8 h-8 text-gray-400 group-hover:text-white transition-colors" />
                <span className="text-xs font-mono text-gray-500 border border-gray-700 px-2 py-1 rounded">{param}</span>
            </div>
            <h3 className="text-2xl font-bold text-white mb-3">{title}</h3>
            <p className="text-gray-400 leading-relaxed text-sm">{desc}</p>
        </div>
    )
}

function ProcessStep({ number, title, desc, icon: Icon }: any) {
    return (
        <div className="flex flex-col md:flex-row gap-6 md:items-start group">
            <div className="shrink-0 flex items-center justify-center w-16 h-16 rounded-2xl bg-white/5 border border-white/10 text-2xl font-bold font-mono text-primary group-hover:scale-110 transition-transform">
                {number}
            </div>
            <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                    <Icon className="w-5 h-5 text-gray-400 group-hover:text-primary transition-colors" />
                    <h3 className="text-xl font-bold text-white">{title}</h3>
                </div>
                <p className="text-gray-400 leading-relaxed max-w-2xl">{desc}</p>
            </div>
        </div>
    )
}
