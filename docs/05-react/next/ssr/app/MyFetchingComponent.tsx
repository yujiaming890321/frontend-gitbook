import React from 'react'

async function getData() {
    const res = await fetch('https://httpbin.org/json')
    return (await res.json()).slideshow.title
}

/* With Server Components, you can read the data and render it in the component */
async function MyServerFetchingComponent() {
    const data = await getData()
    console.log('Console in server component')
    return (
        <div>
            <p>We fetch from the server:</p>
            <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
    )
}

function MyClientFetchingComponent() {
    const [data, setData] = React.useState(null)
    console.log('Console in client component')
    React.useEffect(function fetchEffect() {
        ;(async function () {
            const data = await getData()
            setData(data)
        })()
    }, [])
    return (
        <div>
            <p>We fetch from the client:</p>
            <pre>{JSON.stringify(data, null, 2)}</pre>
        </div>
    )
}

export const MyFetchingComponent = ({ ...props }) => {
    try {
        React.useEffect(() => {}, [])
    } catch (e) {
        return <MyServerFetchingComponent {...props} />
    }
    return <MyClientFetchingComponent {...props} />
}
