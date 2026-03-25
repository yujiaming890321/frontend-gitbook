# Animated

## basis of Animation

### set value

const translation = useRef(new Animated.Value(0)).current;

### replace `View` with an `Animated.View`

<Animated.View></Animated.View>

### `Animated.timing`

Animated.timing(translation, {
    toValue: 50,
}).start();

### useNativeDriver

makes your animations run on the UI thread directly

Animated.timing(translation, {
    toValue: 50,
    useNativeDriver: true,
}).start();

## Animation types

### delay\duration

Animated.timing(translation, {
    toValue: 100,
    delay: 2000,
    duration: 1000,
    useNativeDriver: true,
}).start();

### Easing

Animated.timing(translation, {
    toValue: 100,
    easing: Easing.bounce,
    useNativeDriver: true,
  }).start();

### `Animated.spring`

Just like timed animations, you can play with different parameters such as the friction, speed, or even bounciness of the movement.

Animated.spring(translation, {
  toValue: 100,
  useNativeDriver: true,
}).start();

### `Animated.sequence` and `Animated.parallel`

To animate in sequence, all you need is to pass a list of animations objects to `Animated.sequence`

Animated.sequence([
    Animated.spring(translation.x, {
      toValue: -100,
      useNativeDriver: true,
    }),
    Animated.spring(translation.y, {
      toValue: -100,
      useNativeDriver: true,
    }),
]).start();

`Animated.parallel` works just the same to run multiple animations all at once

Animated.parallel([
  Animated.spring(translation.x, {
    toValue: -100,
    useNativeDriver: true,
  }),
  Animated.spring(translation.y, {
    toValue: -100,
    useNativeDriver: true,
  }),
]).start();

combine sequenced and parallel animations together

Animated.sequence([
  Animated.spring(translation.x, {
    toValue: -100,
    useNativeDriver: true,
  }),
  Animated.parallel([
    Animated.spring(translation.x, {
      toValue: 100,
      useNativeDriver: true,
    }),
    Animated.spring(translation.y, {
      toValue: -100,
      useNativeDriver: true,
    }),
  ]),
]).start();

### `Animated.stagger`

 if you have a series of blocks that you want to nicely fade-in from top to bottom, you could use Animated.stagger which we’ll try right now.

Animated.stagger(1000, [
    Animated.timing(firstOpacity, {
      toValue: 1,
      useNativeDriver: true,
    }),
    Animated.timing(secondOpacity, {
      toValue: 1,
      useNativeDriver: true,
    }),
    Animated.timing(thirdOpacity, {
      toValue: 1,
      useNativeDriver: true,
    }),
  ]).start();

## Interpolation with ReactNative Animations

### .interpolate()

<Animated.View
    style={{
    width: 100,
    height: 100,
    backgroundColor: 'orange',
    transform: [
        { translateX: translation },
    ],
    }}
/>

while this animation is playing, is to also change the opacity and rotate this square.

The problem is that I can’t set the opacity to `translation`, because opacity goes from 0 to 1, not from 0 to 100:

opacity: translation,

To interpolate our translation, we can use .interpolate on any animated value:

opacity: translation.interpolate(),

Interpolating needs two things: the x-s, the input range, and f(x)-s, the output range

opacity: translation.interpolate({
  inputRange: [0, 100],
  outputRange: [0, 1],
}),

For example, let’s say we want the opacity to start at 0, then 1 at 50 pixels, and finally 0 again when it reaches 100. To do so, we need to add another x, 50, and change our outputs

opacity: translation.interpolate({
  inputRange: [0, 50, 100],
  outputRange: [0, 1, 0],
}),

### a tricky reason

this one is a bit tricky for one reason which is: Animated cannot animate some style properties with native driven animations.

This means that if you animate a `backgroundColor` property using the native driver, you should get an error saying that some properties cannot be animated this way.

In this case, all you need is to set useNativeDriver to false

useEffect(() => {
  Animated.timing(translation, {
    toValue: 100,
    duration: 1000,
    useNativeDriver: false,
    backgroundColor: translation.interpolate({
        inputRange: [0, 100],
        outputRange: ['orange', 'blue'],
    }),
  }).start();
}, []);

### extrapolation

opacity: translation.interpolate({
  inputRange: [25, 50, 100],
  outputRange: [0, 1, 0],
  extrapolateLeft: 'clamp',
  extrapolateRight: 'clamp',
}),

extend on both sides is to use the extrapolate property:

opacity: translation.interpolate({
  inputRange: [25, 50, 100],
  outputRange: [0, 1, 0],
  extrapolate: 'clamp',
}),

## ScrollView

we have a long scroll view component, and whenever we scroll down to a certain point, a header should appear at the top of the screen. When we go up again, it should disappear.

const [headerShown, setHeaderShown] = useState(false);
  const translation = useRef(new Animated.Value(-100)).current;
  
  useEffect(() => {
    Animated.timing(translation, {
      toValue: headerShown ? 0 : -100,
      duration: 250,
      useNativeDriver: true,
    }).start();
  }, [headerShown]);

### Animated.event

const scrolling = useRef(new Animated.Value(0)).current;
const translation = scrolling.interpolate({
  inputRange: [100, 130],
  outputRange: [-100, 0],
  extrapolate: 'clamp',
});

onScroll={Animated.event(
  [{
    nativeEvent: {
      contentOffset: {
        y: scrolling,
      },
    },
  }],
  { useNativeDriver: true },
)}

## Gestures

### responder

A very important concept for React Native gestures is called a responder.

