# -*- coding: utf-8 -*-
import datetime
from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RepairModule(models.Model):
    _name = 'repair.module'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Warranty Claim'

    name = fields.Char(string="RO No.", default=lambda self: _('new'))
    partner_id = fields.Many2one('res.partner', string="Customer")
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    product_id = fields.Many2one('product.product', string="Product")
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    brand_id = fields.Many2one(related='product_id.brand_id', string="Brand")
    description = fields.Text(string="Fault Detail")
    repair_line_ids = fields.One2many('repair.module.line', 'repair_parent_id', string="Repair Lines")
    categ_id = fields.Many2one(related='product_id.categ_id', string="Category")
    # date = fields.Datetime(string="Estimated Delivery Time")
    date = fields.Date(string="Estimated Delivery Time", required=True)
    boolean_date = fields.Boolean(default=False, compute="_compute_delivery_date")
    registration_date = fields.Date(string="Registration Date", default=date.today())
    # closed_date = fields.Date(string="Closed Date")
    orders_count = fields.Char(string="Order Count", compute='_compute_order_count')
    delivery_order_count = fields.Char(string="Order Count", compute='_compute_delivery_order_count')
    receipt_order_count = fields.Char(string="Order Count", compute='_compute_receipt_order_count')
    is_faulty_received = fields.Boolean(store=True)
    state = fields.Selection(
        [('draft', 'draft'),
         ('confirmed', 'Confirmed'),
         ('received_faulty', 'Received Faulty Product/s'),
         ('sent_to_supplier', 'Sent to Supplier'),
         ('claimed_from_supplier', 'Claimed From Supplier'),
         ('returned', 'Returned'),
         ('replaced', 'Replaced'),
         ('closed', 'Closed')], default='draft', string="Status")

    def _compute_delivery_date(self):
        today = datetime.date.today()
        for rec in self:
            if rec.date >= today:
                rec.boolean_date = True
            else:
                rec.boolean_date = False


    def action_closed(self):
        for line in self.repair_line_ids:
            line.order_id.repair_count+=1
        self.state = 'closed'

    def received_from_supplier(self):
        self.state = 'claimed_from_supplier'

    def action_open_repair_record(self):
        for rec in self:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Bills',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'domain': [('repair_id', '=', rec.id)],
                'target': 'current',
            }

    def _compute_order_count(self):
        for rec in self:
            # account = self.env['account.move'].search_count([('repair_id', '=', rec.id)])
            account = self.env['account.move'].search_count([('repair_id', '=', rec.id)])
            if account:
                rec.orders_count = account
            else:
                self.orders_count = 0

    def action_open_repair_delivery_record(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Delivery Orders',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('repair_delivery_id', '=', self.id)],
            'target': 'current',
        }

    def _compute_delivery_order_count(self):
        for rec in self:
            # account = self.env['account.move'].search_count([('repair_id', '=', rec.id)])
            account = self.env['stock.picking'].search_count([('repair_delivery_id', '=', rec.id)])
            if account:
                rec.delivery_order_count = account
            else:
                self.delivery_order_count = 0

    def action_open_repair_receipt_record(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Receipts',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('repair_receipt_id', '=', self.id)],
            'target': 'current',
        }

    def _compute_receipt_order_count(self):
        for rec in self:
            # account = self.env['account.move'].search_count([('repair_id', '=', rec.id)])
            account = self.env['stock.picking'].search_count([('repair_receipt_id', '=', rec.id)])
            if account:
                rec.receipt_order_count = account
            else:
                self.receipt_order_count = 0

    def action_repair_cron(self):
        records = self.env['repair.module'].search([])
        # today = datetime.today()
        today = date.today()
        for rec in records:
            if rec.date >= today:
                rec.action_send_email()
                activity = self.env['mail.activity'].sudo().create({
                    'activity_type_id': 4,
                    'summary': 'Warranty Claim',
                    'date_deadline': datetime.datetime.now(),
                    'user_id': rec.user_id.id,
                    'res_id': rec.id,
                    'res_model_id': self.env['ir.model'].search([('model', '=', 'repair.module')], limit=1).id,
                    'res_name': 'activity',
                    'res_model': 'repair.module',
                    'display_name': 'Warranty Claim'
                })

    def action_faulty_location(self):
        location = self.env['stock.location'].search([])
        customer_location = self.partner_id.property_stock_customer
        vendor = self.vendor_id.property_stock_supplier
        type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming')])[0]
        dest_location = self.env["ir.config_parameter"].sudo().get_param("faulty_location_id")
        if dest_location:
            dest_location_id = int(dest_location)
        else:
            raise ValidationError('Please configure location for faulty product in settings.')
        my_list = []
        for rec in self:
            for line in rec.repair_line_ids:
                my_list.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.uom_qty,
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                }))
            picking = self.env['stock.picking'].create({
                'partner_id': rec.vendor_id.id,
                'scheduled_date': rec.date,
                'location_id': customer_location.id,
                'location_dest_id': dest_location_id,
                'picking_type_id': type_id.id,
                'move_ids_without_package': my_list,
                'repair_receipt_id': rec.id
            })
            rec.is_faulty_received = True
            rec.state = 'received_faulty'
            return True

    def action_returned(self):
        if self.repair_line_ids:
            warehouse_id = self.repair_line_ids[0].order_id.warehouse_id.id
            out_picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'outgoing'), ('warehouse_id', '=', warehouse_id)])
            in_picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'), ('warehouse_id', '=', warehouse_id)])
            if out_picking_type:
                src_location = out_picking_type[0].default_location_src_id.id
            else:
                out_picking_type = self.env['stock.picking.type'].search(
                    [('code', '=', 'outgoing')])
                src_location = out_picking_type[0].default_location_src_id.id
            if in_picking_type:
                in_dest_location = in_picking_type[0].default_location_dest_id.id
            else:
                in_picking_type = self.env['stock.picking.type'].search(
                    [('code', '=', 'incoming')])
                in_dest_location = in_picking_type[0].default_location_dest_id.id
        else:
            raise ValidationError('There is not line to process.')
        customer_location = self.partner_id.property_stock_customer
        available_qty = self.product_id.with_context({'location': src_location}).qty_available
        if not available_qty:
            raise UserError(_('Product is not available please contact the supplier.'))
        else:
            out_list = []
            move_list = []
            for line in self.repair_line_ids:
                move_list.append((0, 0, {
                    'product_id': line.product_id.id,
                    'quantity': line.uom_qty,
                    'price_unit': line.product_id.standard_price,
                }))
                out_list.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.uom_qty,
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                }))

            pick_out = self.env['stock.picking'].create({
                'partner_id': self.partner_id.id,
                'scheduled_date': self.date,
                'location_id': src_location,
                'location_dest_id': customer_location.id,
                'picking_type_id': out_picking_type[0].id,
                'move_ids_without_package': out_list,
                'repair_delivery_id': self.id,
            })
            pick_in = self.env['stock.picking'].create({
                'partner_id': self.vendor_id.id,
                'scheduled_date': self.date,
                'location_id': self.vendor_id.property_stock_supplier.id,
                'location_dest_id': in_dest_location,
                'picking_type_id': in_picking_type[0].id,
                'move_ids_without_package': out_list,
                'repair_receipt_id': self.id,
            })
            self.env['account.move'].create({
                'move_type': 'in_invoice',
                'partner_id': self.vendor_id.id,
                'name': self.name,
                'invoice_date': self.date,
                'date': self.date,
                'invoice_line_ids': move_list,
                'repair_id': self.id
            })
            self.state = 'returned'
            a = 1
            # account = self.env['account.move'].search([])
            # for order in purchase.order_line:
            #     for rec in self:
            #         for line in rec.repair_line_ids:
            #             pick_list.append((0, 0, {
            #                 'product_id': line.product_id.id,
            #                 'product_uom_qty': line.uom_qty,
            #                 'product_uom': line.product_id.uom_id.id,
            #                 'name': line.product_id.name
            #             }))
            #             my_list.append((0, 0, {
            #                 'product_id': line.product_id.id,
            #                 'quantity': line.uom_qty,
            #                 'price_unit': order.price_unit,
            #             }))
            #             out_list.append((0, 0, {
            #                 'product_id': line.product_id.id,
            #                 'product_uom_qty': line.uom_qty,
            #                 'name': line.product_id.name,
            #                 'product_uom': line.product_id.uom_id.id,
            #             }))
            #
            #         self.env['stock.picking'].create({
            #             'partner_id': rec.vendor_id.id,
            #             'scheduled_date': rec.date,
            #             # 'location_id': type_id.default_location_src_id.id,
            #             'location_id': customer_location.id,
            #             # 'location_dest_id': type_id.default_location_dest_id.id,
            #             'location_dest_id': type_id.default_location_dest_id.id,
            #             'picking_type_id': type_id.id,
            #             'repair_receipt_id': rec.id,
            #             # 'location_dest_id': pick.location_id.id,
            #             'move_ids_without_package': pick_list
            #         })
            #
            #         self.env['account.move'].create({
            #             'move_type': 'in_invoice',
            #             'partner_id': rec.vendor_id.id,
            #             'name': rec.name,
            #             'invoice_date': rec.date,
            #             'date': rec.date,
            #             'invoice_line_ids': my_list,
            #             'repair_id': rec.id
            #         })
            #         pick_out = self.env['stock.picking'].create({
            #             'partner_id': rec.vendor_id.id,
            #             'scheduled_date': rec.date,
            #             'location_id': type_out.default_location_src_id.id,
            #             # 'location_id': pick.location_id.id,
            #             'location_dest_id': customer_location.id,
            #             'picking_type_id': type_out.id,
            #             'move_ids_without_package': out_list,
            #             'repair_delivery_id': rec.id,
            #             # 'location_dest_id': pick.location_id.id,
            #         })
            #     self.state = 'returned'
            #     return True

    def action_replaced(self):
        my_list = []
        in_list = []
        if self.repair_line_ids:
            warehouse_id = self.repair_line_ids[0].order_id.warehouse_id.id
            in_picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'), ('warehouse_id', '=', warehouse_id)])
            if in_picking_type:
                in_dest_location = in_picking_type[0].default_location_dest_id.id
            else:
                in_picking_type = self.env['stock.picking.type'].search(
                    [('code', '=', 'incoming')])
                in_dest_location = in_picking_type[0].default_location_dest_id.id
        else:
            raise ValidationError('There is not line to process.')
        for line in self.repair_line_ids:
            my_list.append((0, 0, {
                'product_id': line.product_id.id,
                'quantity': line.uom_qty,
                'price_unit': line.product_id.standard_price,
            }))
            in_list.append((0, 0, {
                'product_id': line.product_id.id,
                'product_uom_qty': line.uom_qty,
                'name': line.product_id.name,
                'product_uom': line.product_id.uom_id.id,
            }))
        pick_in = self.env['stock.picking'].create({
            'partner_id': self.vendor_id.id,
            'scheduled_date': self.date,
            'location_id': self.vendor_id.property_stock_supplier.id,
            'location_dest_id': in_dest_location,
            'picking_type_id': in_picking_type[0].id,
            'move_ids_without_package': in_list,
            'repair_receipt_id': self.id,
        })
        self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': self.vendor_id.id,
            'name': self.name,
            'invoice_date': self.date,
            'date': self.date,
            'invoice_line_ids': my_list,
            'repair_id': self.id
        })
        self.state = 'sent_to_supplier'
        return

    def deliever_to_customer(self):
        if self.repair_line_ids:
            warehouse_id = self.repair_line_ids[0].order_id.warehouse_id.id
            out_picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'outgoing'), ('warehouse_id', '=', warehouse_id)])

            if out_picking_type:
                src_location = out_picking_type[0].default_location_src_id.id
            else:
                out_picking_type = self.env['stock.picking.type'].search(
                    [('code', '=', 'outgoing')])
                src_location = out_picking_type[0].default_location_src_id.id
        else:
            raise ValidationError('There is not line to process.')
        customer_location = self.partner_id.property_stock_customer
        available_qty = self.product_id.with_context({'location': src_location}).qty_available
        if not available_qty:
            raise UserError(_('Product is not available please contact the supplier.'))
        else:
            out_list = []
            for line in self.repair_line_ids:
                out_list.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.uom_qty,
                    'name': line.product_id.name,
                    'product_uom': line.product_id.uom_id.id,
                }))

            pick_out = self.env['stock.picking'].create({
                'partner_id': self.partner_id.id,
                'scheduled_date': self.date,
                'location_id': src_location,
                'location_dest_id': customer_location.id,
                'picking_type_id': out_picking_type[0].id,
                'move_ids_without_package': out_list,
                'repair_delivery_id': self.id,
            })

            self.state = 'replaced'

    def action_draft(self):
        self.state = 'draft'

    def action_confirm(self):
        self.state = 'confirmed'
        # my_list=[]
        # type_id = self.env['stock.picking.type'].search([('code', '=', 'incoming')])[0]
        # for rec in self:
        #     for line in rec.repair_line_ids:
        #         my_list.append((0, 0, {
        #             'product_id': line.product_id.id,
        #             'product_uom_qty': line.uom_qty,
        #             'product_uom': line.product_id.uom_id.id,
        #             'name': line.product_id.name
        #         }))
        #     picking = self.env['stock.picking'].create({
        #         'partner_id': rec.vendor_id.id,
        #         'scheduled_date': rec.date,
        #         'location_id': type_id.default_location_src_id.id,
        #         # 'location_id': pick.location_id.id,
        #         'location_dest_id': type_id.default_location_dest_id.id,
        #         'picking_type_id': type_id.id,
        #         # 'location_dest_id': pick.location_id.id,
        #         'move_ids_without_package': my_list
        #     })
        #     return picking

    def action_send_email(self):
        records = self.env['repair.module'].search([])
        # today = datetime.today()
        today = date.today()
        for rec in records:
            if rec.registration_date == today:
                template_id = self.env.ref('repair_module.email_template_repair_module').id
                self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
                print('email has been sent.......')
            # if rec.closed_date == today:
            #     template_id = self.env.ref('repair_module.email_template_repair_module_closed_date').id
            #     self.env['mail.template'].browse(template_id).send_mail(self.id, force_send=True)
            #     print('email has been sent.......')

    @api.model
    def create(self, vals):
        if vals.get('name', _('new')) == _('new'):
            vals['name'] = self.env['ir.sequence'].next_by_code('repair.module') or _('new')
        rep = super(RepairModule, self).create(vals)
        return rep

    @api.onchange('product_id', 'partner_id')
    def get_same_product(self):
        if self.partner_id and self.product_id:
            self.repair_line_ids = False
            sale_orders = self.env['sale.order'].search([('partner_id', '=', self.partner_id.id),
                                                         ('order_line.product_uom_qty', '>', 0),
                                                         ('order_line.product_id', '=', self.product_id.id)])

            my_list = []
            if sale_orders:
                for sale_order in sale_orders:
                    if sale_order.state == 'sale' or sale_order.state == 'done':
                        for line in sale_order.order_line:
                            if line.product_id.id == self.product_id.id:
                                my_list.append((0, 0, {
                                    'default_code': line.product_id.default_code,
                                    'product_id': line.product_id.id,
                                    'order_id': sale_order.id,
                                    'uom_qty': line.product_uom_qty
                                }))

            self.update({'repair_line_ids': my_list})


class RepairModuleLine(models.Model):
    _name = 'repair.module.line'
    _description = 'repair_module line description'

    default_code = fields.Char(string='Old Serial No.')
    new_code = fields.Char(string='New Serial No.')
    order_id = fields.Many2one('sale.order', string='SO. No.')
    product_id = fields.Many2one('product.product', string="Product")
    uom_qty = fields.Float(string='Quantity')
    repair_count = fields.Integer(related="order_id.repair_count",string='No. of Repairs')
    repair_parent_id = fields.Many2one('repair.module', string="parent id")


class RepairAccountMove(models.Model):
    _inherit = 'account.move'

    repair_id = fields.Many2one('repair.module', string="Self_id")


class RepairStockPicking(models.Model):
    _inherit = 'stock.picking'

    repair_receipt_id = fields.Many2one('repair.module', string="Repair id")
    repair_delivery_id = fields.Many2one('repair.module', string="Self_id")

class SaleOrder(models.Model):
    _inherit = "sale.order"
    repair_count = fields.Integer()