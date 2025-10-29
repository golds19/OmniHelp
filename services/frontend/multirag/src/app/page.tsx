"use client";
import React, { useEffect, useState } from "react";

export default function Home() {
	const [backendStatus, setBackendStatus] = useState("Testing...");

	useEffect(() => {
		console.log("🔄 Starting backend connectivity test...");
		console.log("📡 Attempting to fetch from: http://localhost:8000/ping");
		
		fetch("http://localhost:8000/ping")
			.then((res) => {
				console.log("✅ Response received:", res);
				console.log("📊 Response status:", res.status);
				console.log("📋 Response ok:", res.ok);
				return res.json();
			})
			.then((data) => {
				console.log("📦 Parsed JSON data:", data);
				console.log("💬 Message from backend:", data.message);
				setBackendStatus(data.message || "No response");
			})
			.catch((error) => {
				console.error("❌ Error occurred:", error);
				console.error("🔍 Error name:", error.name);
				console.error("📝 Error message:", error.message);
				setBackendStatus("Backend unreachable");
			});
	}, []);

	console.log("🎨 Component rendering with status:", backendStatus);

	return (
		<main style={{ minHeight: "100vh", display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center" }}>
			<h1>Backend Connectivity Test</h1>
			<p>Status: <b>{backendStatus}</b></p>
		</main>
	);
}