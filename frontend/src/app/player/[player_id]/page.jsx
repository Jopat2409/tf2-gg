"use client"
import { useEffect, useState } from "react";

export default function PlayerDetails({params}) {
    const player_id = params.player_id;

    const [playerData, setPlayerData] = useState({})
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        const loadData = async () => {
            const response = await fetch(`https://api.rgl.gg/v0/profile/${player_id}`);
            const data = await response.json()
            setPlayerData(data)
            setLoading(false);
        }

        loadData();
    }, [])

    return loading ? (
        <h1> Loading... </h1>
    ) : (
        <img src={playerData.avatar}/>
    )
}
