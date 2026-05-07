import { useEffect, useState } from "react";
import { type View, viewFromPath, viewRoutes } from "../constants";

export function useAppRoute() {
  const [view, setView] = useState<View>(() => viewFromPath(window.location.pathname));

  function navigateTo(nextView: View, replace = false) {
    const nextPath = viewRoutes[nextView];
    if (window.location.pathname !== nextPath) {
      const method = replace ? "replaceState" : "pushState";
      window.history[method](null, "", nextPath);
    }
    setView(nextView);
  }

  useEffect(() => {
    const syncRoute = () => setView(viewFromPath(window.location.pathname));
    window.addEventListener("popstate", syncRoute);
    if (!Object.values(viewRoutes).includes(window.location.pathname)) {
      navigateTo(view, true);
    }
    return () => window.removeEventListener("popstate", syncRoute);
  }, []);

  return { view, navigateTo };
}
