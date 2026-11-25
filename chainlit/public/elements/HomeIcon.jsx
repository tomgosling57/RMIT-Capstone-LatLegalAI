import { Button } from "@/components/ui/button"
import { Home } from 'lucide-react';

export default function HomeIcon({ href, target, tooltip }) {
    return (
        <div id="home-icon" className="fixed z-50" style={{ "right": "180px", "top": "12px"}}>
            <a href={href || "http://localhost:5000"} target={target || "_self"}>
                <Button
                    variant="outline"
                    size="icon"
                    className="rounded-full border-0 bg-transparent hover:bg-transparent transition-all duration-200"
                    title={tooltip || "Go to LatMatrix homepage"}
                    style={{ width: "32px", height: "32px" }}
                >
                    <Home style={{ width: "24px", height: "24px", color: "hsl(0, 0%, 67%)" }} />
                </Button>
            </a>
        </div>
    );
}
