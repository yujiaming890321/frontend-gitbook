# useReducer

const initState = {
    a: { userId: null, show: false }
};

const reducer = (state, action) => {
    switch (action.type) {
        case 'a':
            return { ...state, a: { show: false, userId: null } };
        default :
            return { ...state };
    }
};
const [ state, dispatch ] = useReducer(reducer, initState);