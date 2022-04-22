import React from 'react'
import { render, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import configureStore from 'redux-mock-store'
import { Provider } from 'react-redux'
import * as Redux from 'react-redux'
import AuxiliaryMaterialsEnterList from '../index'

let once = {
	queryItems: 1,
	useDidHide: 1,
}
// mock taro
jest.mock('@tarojs/taro', () => ({
	__esModule: true,
	default: {
		getSystemInfo: () => {
			return {
				screenHeight: '800',
			}
		},
		getSystemInfoSync: () => {
			return {
				statusBarHeight: '80',
			}
		},
		getCurrentPages: () => [{ route: '' }],
	},
	usePageScroll: jest.fn(),
	useDidHide: (callback: any) => {
		if (once.useDidHide <= 1) {
			once.useDidHide++
			callback()
		}
	},
}))
// mock 工具
jest.mock('@/common/utils', () => ({
	__esModule: true,
	default: {
		sleep: jest.fn(),
	},
	throttleFn: (callback: any) => {
		callback()
	},
}))
// mock 其他组件
jest.mock(
	'@/pages/task/auxiliaryMaterialsEnterList/components/listGroup',
	() => require('./MockListGroup').default
)
// mock service
jest.mock('@/pages/task/auxiliaryMaterialsEnterList/service', () => ({
	__esModule: true,
	default: {
		queryItems: () => {
			const data = require('root/mock/auxiliaryMaterialMall').default[
				'POST /purchase/queryItems'
			].data

			if (once.queryItems <= 2) {
				once.queryItems++
			} else if (once.queryItems <= 4) {
				once.queryItems++
				data.total = 21
				data.pageIndex = 2
			} else {
				data.total = 1
			}

			return data
		},
		querySites: jest.fn(),
	},
}))
// mock dispatch
jest.spyOn(Redux, 'useDispatch').mockImplementation((): any => {
	return {
		modalStatus: {
			searchText: 'a2',
			setSearchTextAsync: jest.fn(),
		},
	}
})
// 定义初始化数据
const initState = {
	modalStatus: {
		searchBorderRadius: '',
	},
	workerOrderList: {
		showAccessoryEntry: '',
	},
}

// store 数据模拟
const mockStore = configureStore([])
const store = mockStore(initState)

// mocha 语法
describe('AuxiliaryMaterialsEnterList', () => {
	test('无参数时', async () => {
		jest.useFakeTimers()
		const { container } = render(
			<Provider store={store}>
				<AuxiliaryMaterialsEnterList></AuxiliaryMaterialsEnterList>
			</Provider>
		)

		await waitFor(() => {
			const btn = container.querySelector('.delete-text')
			expect(btn).not.toBeNull()
			if (btn) {
				userEvent.click(btn)
			}

			expect(
				container.querySelectorAll('.auxiliary-materialsl-enter-list')
			).toHaveLength(1)
		})
	})
})
