import '../globals.css';
import './shop.css';
import ShopHeader from '../../components/shop/ShopHeader';

export default function ShopLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="shop-body">
      <ShopHeader />
      <main className="shop-main">{children}</main>
      <p className="shop-footer-note" style={{ maxWidth: 1120, margin: '0 auto', padding: '0 1.5rem 2rem' }}>
        Customer checkout traffic is sent through the API gateway. Security operations live on a separate dashboard.
      </p>
    </div>
  );
}
