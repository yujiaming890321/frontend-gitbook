'use client'
import { MyFetchingComponent } from './MyFetchingComponent'

export default function ClientSection() {
    return (
        <div>
            <p>This is rendered on the client (use client)</p>
            <MyFetchingComponent />
        </div>
    )
}
