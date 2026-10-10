'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { clearSession, getShopUser, ShopUser } from '../../lib/shopApi';

export default function ShopHeader() {
  const pathname = usePathname();
  const [user, setUser] = useState<ShopUser | null>(null);

  useEffect(() => {
    setUser(getShopUser());
  }, [pathname]);

  return (
    <header className="shop-header">
      <div className="shop-header-inner">
        <Link href="/shop" className="shop-logo">
          Aurora Boutique
        </Link>
        <nav className="shop-nav">
          <Link href="/shop">Catalog</Link>
          <Link href="/shop/cart">Cart</Link>
          <Link href="/shop/orders">Orders</Link>
          {user ? (
            <>
              <span>Hi, {user.username}</span>
              <button
                type="button"
                onClick={() => {
                  clearSession();
                  setUser(null);
                  window.location.href = '/shop';
                }}
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link href="/shop/login">Sign in</Link>
              <Link href="/shop/register">Create account</Link>
            </>
          )}
        </nav>
      </div>
    </header>
  );
}
