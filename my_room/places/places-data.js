// places tiffany has been + wants to go. hand-curated from her "places to go" PDF
// (OCR'd 6/24/26) + travel memory. lat/lon are approximate — good enough for dots.
// to refresh: re-OCR the PDF and update this file. coords as [lat, lon].
window.PLACES = {
  generated: "2026-06-24",
  home: { name: "Egypt", note: "home base — back every ~5 years", lat: 30.04, lon: 31.24 },
  been: [
    // — Europe —
    { name: "London", region: "UK", lat: 51.51, lon: -0.13 },
    { name: "Edinburgh", region: "UK", lat: 55.95, lon: -3.19 },
    { name: "Newcastle", region: "UK", lat: 54.98, lon: -1.61 },
    { name: "Stratford-upon-Avon", region: "UK", lat: 52.19, lon: -1.71 },
    { name: "Alnwick", region: "UK", lat: 55.41, lon: -1.71 },
    { name: "Amsterdam", region: "Europe", lat: 52.37, lon: 4.90 },
    { name: "Athens", region: "Europe", lat: 37.98, lon: 23.73 },
    { name: "Copenhagen", region: "Europe", lat: 55.68, lon: 12.57 },
    { name: "Madrid", region: "Europe", lat: 40.42, lon: -3.70 },
    { name: "Hanover", region: "Europe", lat: 52.37, lon: 9.73 },
    // — North America —
    { name: "San Francisco", region: "USA", lat: 37.77, lon: -122.42 },
    { name: "San Diego", region: "USA", lat: 32.72, lon: -117.16 },
    { name: "Los Angeles", region: "USA", lat: 34.05, lon: -118.24 },
    { name: "San Jose", region: "USA", lat: 37.34, lon: -121.89 },
    { name: "Napa & Sonoma", region: "USA", lat: 38.30, lon: -122.40 },
    { name: "Malibu", region: "USA", lat: 34.03, lon: -118.69 },
    { name: "Orlando", region: "USA", lat: 28.54, lon: -81.38 },
    { name: "Denver & Boulder", region: "USA", lat: 39.74, lon: -104.99 },
    { name: "New Orleans", region: "USA", lat: 29.95, lon: -90.07 },
    { name: "Chicago", region: "USA", lat: 41.88, lon: -87.63 },
    { name: "Las Vegas", region: "USA", lat: 36.17, lon: -115.14 },
    { name: "Philadelphia", region: "USA", lat: 39.95, lon: -75.16 },
    { name: "Puerto Rico", region: "Caribbean", lat: 18.47, lon: -66.11 },
    // — Asia —
    { name: "Tokyo", region: "Asia", lat: 35.68, lon: 139.69 },
    { name: "Singapore", region: "Asia", lat: 1.35, lon: 103.82 }
  ],
  wishlist: [
    // — Italy circuit (most-planned) —
    { name: "Rome", region: "Italy", lat: 41.90, lon: 12.50 },
    { name: "Venice", region: "Italy", lat: 45.44, lon: 12.34 },
    { name: "Florence", region: "Italy", lat: 43.77, lon: 11.26 },
    { name: "Naples & Capri", region: "Italy", lat: 40.85, lon: 14.27 },
    { name: "Sicily", region: "Italy", lat: 38.12, lon: 13.36 },
    { name: "Milan", region: "Italy", lat: 45.46, lon: 9.19 },
    // — rest of Europe —
    { name: "Paris", region: "France", lat: 48.86, lon: 2.35 },
    { name: "Nice", region: "France", lat: 43.71, lon: 7.26 },
    { name: "Barcelona", region: "Spain", lat: 41.39, lon: 2.17 },
    { name: "Granada", region: "Spain", lat: 37.18, lon: -3.60 },
    { name: "Lisbon", region: "Portugal", lat: 38.72, lon: -9.14 },
    { name: "Porto", region: "Portugal", lat: 41.16, lon: -8.61 },
    { name: "Berlin", region: "Germany", lat: 52.52, lon: 13.40 },
    { name: "Munich", region: "Germany", lat: 48.14, lon: 11.58 },
    { name: "Vienna", region: "Austria", lat: 48.21, lon: 16.37 },
    { name: "Prague", region: "Czechia", lat: 50.08, lon: 14.44 },
    { name: "Geneva", region: "Switzerland", lat: 46.20, lon: 6.14 },
    { name: "Gdańsk", region: "Poland", lat: 54.35, lon: 18.65 },
    { name: "Dublin", region: "Ireland", lat: 53.35, lon: -6.26 },
    { name: "Oslo & Lofoten", region: "Norway", lat: 61.50, lon: 9.00 },
    { name: "Reykjavík", region: "Iceland", lat: 64.15, lon: -21.94 },
    { name: "Helsinki", region: "Finland", lat: 60.17, lon: 24.94 },
    { name: "Dubrovnik", region: "Croatia", lat: 42.65, lon: 18.09 },
    { name: "Budapest", region: "Hungary", lat: 47.50, lon: 19.04 },
    { name: "Stockholm", region: "Sweden", lat: 59.33, lon: 18.07 },
    { name: "Malta", region: "Malta", lat: 35.90, lon: 14.51 },
    { name: "Monaco", region: "Monaco", lat: 43.74, lon: 7.42 },
    // — North America —
    { name: "Toronto & Montreal", region: "Canada", lat: 44.50, lon: -76.00 },
    { name: "Seattle", region: "USA", lat: 47.61, lon: -122.33 },
    { name: "Tahoe", region: "USA", lat: 39.10, lon: -120.03 },
    { name: "Miami", region: "USA", lat: 25.76, lon: -80.19 },
    { name: "Santa Fe", region: "USA", lat: 35.69, lon: -105.94 },
    { name: "Jackson, WY", region: "USA", lat: 43.48, lon: -110.76 },
    { name: "Hawaii (Oahu)", region: "USA", lat: 21.31, lon: -157.86 },
    // — further afield —
    { name: "Machu Picchu", region: "Peru", lat: -13.16, lon: -72.54 },
    { name: "Cartagena", region: "Colombia", lat: 10.39, lon: -75.51 },
    { name: "Rio de Janeiro", region: "Brazil", lat: -22.91, lon: -43.17 },
    { name: "Cape Town", region: "South Africa", lat: -33.92, lon: 18.42 },
    { name: "Marrakech", region: "Morocco", lat: 31.63, lon: -7.99 },
    { name: "Bali", region: "Indonesia", lat: -8.34, lon: 115.09 },
    { name: "Bangkok", region: "Thailand", lat: 13.76, lon: 100.50 },
    { name: "Sydney", region: "Australia", lat: -33.87, lon: 151.21 },
    { name: "Dubai", region: "UAE", lat: 25.20, lon: 55.27 }
  ]
};
