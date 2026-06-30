import httpx, asyncio, uuid, sys

async def test():
    async with httpx.AsyncClient(timeout=30) as c:
        base = "https://workplace1app.vercel.app"

        # Test 1: Health
        r = await c.get(f"{base}/api/health")
        print(f"[1] Health: {r.status_code} {r.json()}")

        # Test 2: Register
        test_email = f"test_{uuid.uuid4().hex[:8]}@matchmate.test"
        r = await c.post(f"{base}/api/auth/register", json={
            "email": test_email, "password": "Test@1234", "nickname": "TestUser"
        })
        print(f"[2] Register: {r.status_code}")
        data = r.json() if r.status_code < 400 else r.text[:200]
        print(f"    {data}")

        if r.status_code not in (200, 201):
            print("\nRegistration failed, skipping remaining tests")
            return

        # Test 3: Login
        r = await c.post(f"{base}/api/auth/login", json={
            "login": test_email, "password": "Test@1234"
        })
        print(f"[3] Login: {r.status_code}")
        if r.status_code == 200:
            tokens = r.json()
            print(f"    access_token: {tokens['access_token'][:30]}...")

            # Test 4: Refresh
            r = await c.post(f"{base}/api/auth/refresh", json={
                "refresh_token": tokens["refresh_token"]
            })
            print(f"[4] Refresh: {r.status_code} {'OK' if r.status_code==200 else r.text[:100]}")

            # Test 5: Duplicate
            r = await c.post(f"{base}/api/auth/register", json={
                "email": test_email, "password": "Test@1234"
            })
            print(f"[5] Duplicate: {r.status_code} {'(expected 409)' if r.status_code==409 else ''}")
            if r.status_code != 409:
                print(f"    UNEXPECTED: {r.text[:100]}")

            # Test 6: Wrong password
            r = await c.post(f"{base}/api/auth/login", json={
                "login": test_email, "password": "WrongPass1"
            })
            print(f"[6] Wrong pwd: {r.status_code} {'(expected 401)' if r.status_code==401 else ''}")
            if r.status_code != 401:
                print(f"    UNEXPECTED: {r.text[:100]}")

            # Test 7: Weak password
            r = await c.post(f"{base}/api/auth/register", json={
                "email": f"test2_{uuid.uuid4().hex[:8]}@test.com", "password": "123"
            })
            print(f"[7] Weak pwd: {r.status_code} '(expected 422)'")
        else:
            print(f"    Error: {r.text[:200]}")

        # Test 8: Distance (stateless)
        r = await c.get(f"{base}/api/distance?lat1=39.9&lon1=116.4&lat2=31.2&lon2=121.5")
        print(f"[8] Distance: {r.status_code} {r.json()['distance_km']}km")

        # Test 9: Deck sample
        r = await c.get(f"{base}/api/deck/sample")
        data = r.json()
        print(f"[9] Deck: {r.status_code} {len(data['candidates'])} candidates")

    print("\n=== All tests completed ===")

asyncio.run(test())
