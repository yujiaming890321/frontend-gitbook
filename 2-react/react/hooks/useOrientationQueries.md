# 

```js
import { useState, useEffect } from 'react';

const queryList = {
  portrait: '(orientation: portrait)',
  'portrait-primary': '(orientation: portrait-primary)',
  'portrait-secondary': '(orientation: portrait-secondary)',
  landscape: '(orientation: landscape)',
  'landscape-primary': '(orientation: landscape-primary)',
  'landscape-secondary': '(orientation: landscape-secondary)',
};

export const matchMediaQuery = query =>
  typeof window !== 'undefined' ? window.matchMedia(queryList[query]) : { matches: false };

export const getMediaQueryLists = () => ({
  isPortrait:
    matchMediaQuery('portrait') ||
    matchMediaQuery('portrait-primary') ||
    matchMediaQuery('portrait-secondary'),
  isLandscape:
    matchMediaQuery('landscape') ||
    matchMediaQuery('landscape-primary') ||
    matchMediaQuery('landscape-secondary'),
});

export const getMediaQueryMatches = queries =>
  // eslint-disable-next-line no-shadow
  Object.entries(queries).reduce((queries, [query, queryList]) => ({
    ...queries,
    [query]: queryList.matches,
  }));

const useOrientationQueries = () => {
  const initalQueryMatches = getMediaQueryMatches(getMediaQueryLists());
  const [matchingQueries, setMatchingQueries] = useState(initalQueryMatches);

  useEffect(() => {
    // Gets the media queries (not their boolean values) and allows us to bind the change listeners
    const mediaQueries = getMediaQueryLists();

    // When a query fires the change listener, it updates the state with matches
    const onChange = () => {
      setMatchingQueries(prevQueries => ({
        ...prevQueries,
        ...getMediaQueryMatches(mediaQueries),
      }));
    };

    Object.values(mediaQueries).forEach(query => query.addEventListener('change', onChange));

    return () => {
      Object.values(mediaQueries).forEach(query => query.removeEventListener('change', onChange));
    };
  }, []);

  return { ...matchingQueries };
};

export default useOrientationQueries;
```