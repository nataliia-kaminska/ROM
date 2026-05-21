import { useEffect, useState } from "react";
import { opportunityIdFromPath, type View, viewFromPath, viewRoutes } from "../constants";

export function useAppRoute() {
  const [view, setView] = useState<View>(() => viewFromPath(window.location.pathname));
  const [opportunityId, setOpportunityId] = useState<number | null>(() => opportunityIdFromPath(window.location.pathname));

  function navigateTo(nextView: View, replace = false) {
    const nextPath = viewRoutes[nextView];
    if (window.location.pathname !== nextPath) {
      const method = replace ? "replaceState" : "pushState";
      window.history[method](null, "", nextPath);
    }
    setView(nextView);
    setOpportunityId(null);
  }

  function navigateToOpportunity(nextOpportunityId: number, replace = false) {
    const nextPath = `/opportunities/${nextOpportunityId}`;
    if (window.location.pathname !== nextPath) {
      const method = replace ? "replaceState" : "pushState";
      window.history[method](null, "", nextPath);
    }
    setView("opportunity");
    setOpportunityId(nextOpportunityId);
  }

  useEffect(() => {
    const syncRoute = () => {
      setView(viewFromPath(window.location.pathname));
      setOpportunityId(opportunityIdFromPath(window.location.pathname));
    };
    window.addEventListener("popstate", syncRoute);
    if (!Object.values(viewRoutes).includes(window.location.pathname) && !opportunityIdFromPath(window.location.pathname)) {
      navigateTo(view, true);
    }
    return () => window.removeEventListener("popstate", syncRoute);
  }, []);

  return { view, opportunityId, navigateTo, navigateToOpportunity };
}
