import ServerSection from './ServerSection'
import ClientSection from './ClientSection'

export default function Home() {
    return (
        <main className="flex min-h-screen flex-col items-center justify-between p-24">
            <ServerSection />
            <ClientSection />
        </main>
    )
}
